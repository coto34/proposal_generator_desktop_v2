import re
import math
from typing import List, Dict, Any
from dataclasses import dataclass

@dataclass
class TokenLimits:
    DEEPSEEK_CONTEXT = 32000  # DeepSeek context window
    SONNET_CONTEXT = 200000   # Claude Sonnet context window
    SAFETY_MARGIN = 0.8       # Use only 80% of context to be safe
    AVG_CHARS_PER_TOKEN = 4   # Rough estimate: 1 token ≈ 4 characters

class TokenManager:
    """Manages token counting and content chunking for LLM providers"""
    
    @staticmethod
    def estimate_tokens(text: str) -> int:
        """Rough token estimation based on character count"""
        if not text:
            return 0
        return len(text) // TokenLimits.AVG_CHARS_PER_TOKEN
    
    @staticmethod
    def get_max_content_tokens(provider: str, prompt_overhead: int = 1000) -> int:
        """Get maximum tokens available for content after accounting for prompt overhead"""
        if provider.lower() == "deepseek":
            total_limit = int(TokenLimits.DEEPSEEK_CONTEXT * TokenLimits.SAFETY_MARGIN)
        elif provider.lower() == "sonnet":
            total_limit = int(TokenLimits.SONNET_CONTEXT * TokenLimits.SAFETY_MARGIN)
        else:
            total_limit = 8000  # Default conservative limit
            
        return max(total_limit - prompt_overhead, 1000)
    
    @staticmethod
    def intelligent_chunk_tor(tor_content: str, max_tokens_per_chunk: int) -> List[Dict[str, str]]:
        """
        Intelligently chunk ToR content into logical sections
        Returns list of chunks with metadata
        """
        if not tor_content:
            return []
        
        # If content is small enough, return as single chunk
        if TokenManager.estimate_tokens(tor_content) <= max_tokens_per_chunk:
            return [{"content": tor_content, "section": "complete", "index": 0}]
        
        # Try to split by common ToR sections
        chunks = TokenManager._split_by_sections(tor_content)
        
        # If sections are still too large, split by paragraphs
        final_chunks = []
        for i, chunk in enumerate(chunks):
            if TokenManager.estimate_tokens(chunk["content"]) <= max_tokens_per_chunk:
                chunk["index"] = i
                final_chunks.append(chunk)
            else:
                # Further split large sections
                sub_chunks = TokenManager._split_by_paragraphs(
                    chunk["content"], 
                    max_tokens_per_chunk,
                    chunk["section"]
                )
                for j, sub_chunk in enumerate(sub_chunks):
                    sub_chunk["index"] = f"{i}.{j}"
                    final_chunks.append(sub_chunk)
        
        return final_chunks
    
    @staticmethod
    def _split_by_sections(content: str) -> List[Dict[str, str]]:
        """Split content by typical ToR sections"""
        
        # Common ToR section headers (multilingual)
        section_patterns = [
            r'(?i)(?:^|\n)\s*(?:\d+\.?\s*)?(?:background|antecedentes|contexto)',
            r'(?i)(?:^|\n)\s*(?:\d+\.?\s*)?(?:objective|objetivo|propósito)',
            r'(?i)(?:^|\n)\s*(?:\d+\.?\s*)?(?:scope|alcance|ámbito)',
            r'(?i)(?:^|\n)\s*(?:\d+\.?\s*)?(?:methodology|metodología|enfoque)',
            r'(?i)(?:^|\n)\s*(?:\d+\.?\s*)?(?:deliverable|entregable|producto)',
            r'(?i)(?:^|\n)\s*(?:\d+\.?\s*)?(?:timeline|cronograma|calendario)',
            r'(?i)(?:^|\n)\s*(?:\d+\.?\s*)?(?:budget|presupuesto|costo)',
            r'(?i)(?:^|\n)\s*(?:\d+\.?\s*)?(?:qualification|calificación|perfil)',
            r'(?i)(?:^|\n)\s*(?:\d+\.?\s*)?(?:requirement|requisito|condición)',
        ]
        
        # Find all section breaks
        breaks = []
        for pattern in section_patterns:
            for match in re.finditer(pattern, content):
                section_name = TokenManager._extract_section_name(match.group())
                breaks.append((match.start(), section_name))
        
        # Sort breaks by position
        breaks.sort()
        
        if not breaks:
            return [{"content": content, "section": "unknown"}]
        
        # Create chunks based on breaks
        chunks = []
        for i, (start, section_name) in enumerate(breaks):
            if i == 0 and start > 0:
                # Content before first section
                chunks.append({
                    "content": content[:start].strip(),
                    "section": "introduction"
                })
            
            # Current section
            end = breaks[i + 1][0] if i + 1 < len(breaks) else len(content)
            section_content = content[start:end].strip()
            if section_content:
                chunks.append({
                    "content": section_content,
                    "section": section_name
                })
        
        return [chunk for chunk in chunks if chunk["content"]]
    
    @staticmethod
    def _extract_section_name(header: str) -> str:
        """Extract a clean section name from header"""
        # Remove numbers, special chars, normalize
        clean = re.sub(r'^\s*\d+\.?\s*', '', header.strip())
        clean = re.sub(r'[^\w\s]', '', clean).lower()
        return clean[:20] if clean else "section"
    
    @staticmethod
    def _split_by_paragraphs(content: str, max_tokens: int, section_name: str) -> List[Dict[str, str]]:
        """Split large content by paragraphs when sections are too big"""
        paragraphs = [p.strip() for p in content.split('\n\n') if p.strip()]
        
        chunks = []
        current_chunk = ""
        
        for paragraph in paragraphs:
            test_chunk = current_chunk + "\n\n" + paragraph if current_chunk else paragraph
            
            if TokenManager.estimate_tokens(test_chunk) <= max_tokens:
                current_chunk = test_chunk
            else:
                if current_chunk:
                    chunks.append({
                        "content": current_chunk,
                        "section": f"{section_name}_part"
                    })
                current_chunk = paragraph
        
        # Add final chunk
        if current_chunk:
            chunks.append({
                "content": current_chunk,
                "section": f"{section_name}_part"
            })
        
        return chunks

class ChainedPromptGenerator:
    """Handles chained prompts for large documents"""
    
    def __init__(self, client, max_tokens_per_chunk: int):
        self.client = client
        self.max_tokens_per_chunk = max_tokens_per_chunk
        self.accumulated_context = ""
    
    def process_tor_chunks(self, chunks: List[Dict[str, str]], project_info: Dict, task_type: str) -> str:
        """Process multiple ToR chunks and accumulate context"""
        
        if len(chunks) == 1:
            # Single chunk - use direct approach
            return self._generate_single_chunk(chunks[0], project_info, task_type)
        
        # Multiple chunks - use chaining approach
        return self._generate_chained(chunks, project_info, task_type)
    
    def _generate_single_chunk(self, chunk: Dict[str, str], project_info: Dict, task_type: str) -> str:
        """Generate content for single chunk"""
        if task_type == "narrative":
            prompt = self._build_narrative_prompt(chunk["content"], project_info)
        else:
            prompt = self._build_budget_prompt(chunk["content"], project_info)
        
        try:
            if hasattr(self.client, 'generate'):
                result = self.client.generate(prompt)
                return result.content
            else:
                schema = self._get_budget_schema()
                return self.client.generate_json(prompt, schema)
        except Exception as e:
            return f"Error en generación: {str(e)}"
    
    def _generate_chained(self, chunks: List[Dict[str, str]], project_info: Dict, task_type: str) -> str:
        """Generate content using chained prompts"""
        
        # First pass: Extract key information from each chunk
        key_info = []
        for i, chunk in enumerate(chunks):
            print(f"Processing chunk {i+1}/{len(chunks)}: {chunk['section']}")
            
            extraction_prompt = f"""
Analiza este fragmento de los términos de referencia y extrae la información clave:

SECCIÓN: {chunk['section']}
CONTENIDO:
{chunk['content']}

Extrae y resume:
1. Objetivos mencionados
2. Actividades requeridas  
3. Entregables esperados
4. Recursos necesarios
5. Restricciones o condiciones
6. Información presupuestal (si hay)

Responde de forma concisa y estructurada.
"""
            
            try:
                if hasattr(self.client, 'generate'):
                    result = self.client.generate(extraction_prompt)
                    key_info.append(f"SECCIÓN {chunk['section']}:\n{result.content}\n")
                else:
                    # For budget client, still try to extract info
                    key_info.append(f"SECCIÓN {chunk['section']}:\n{chunk['content'][:500]}...\n")
            except Exception as e:
                key_info.append(f"SECCIÓN {chunk['section']}: Error procesando - {str(e)}\n")
        
        # Second pass: Generate final content based on accumulated information
        consolidated_info = "\n".join(key_info)
        
        try:
            if task_type == "narrative":
                final_prompt = self._build_narrative_prompt(consolidated_info, project_info, is_consolidated=True)
                result = self.client.generate(final_prompt)
                return result.content
            else:
                final_prompt = self._build_budget_prompt(consolidated_info, project_info, is_consolidated=True)
                schema = self._get_budget_schema()
                return self.client.generate_json(final_prompt, schema)
        except Exception as e:
            return f"Error en generación consolidada: {str(e)}"
    
    def _build_narrative_prompt(self, content: str, project_info: Dict, is_consolidated: bool = False) -> str:
        """Build narrative generation prompt"""
        content_type = "información consolidada" if is_consolidated else "términos de referencia"
        
        return f"""
Basándote en la siguiente {content_type} y información del proyecto, genera una narrativa completa para una propuesta de proyecto en {project_info.get('language', 'es')}.

INFORMACIÓN DEL PROYECTO:
- Título: {project_info.get('title', '')}
- País: {project_info.get('country', '')}
- Donante: {project_info.get('donor', '')}
- Duración: {project_info.get('duration_months', '')} meses
- Presupuesto máximo: {project_info.get('budget_cap', 'No especificado')}

PERFIL DE LA ORGANIZACIÓN:
{project_info.get('org_profile', '')}

{content_type.upper()}:
{content}

Por favor genera una narrativa completa que incluya:
1. Resumen ejecutivo
2. Justificación del proyecto
3. Objetivos y resultados esperados
4. Metodología
5. Plan de implementación
6. Sostenibilidad
7. Monitoreo y evaluación

La narrativa debe ser profesional, convincente y alineada con los términos de referencia.
"""
    
    def _build_budget_prompt(self, content: str, project_info: Dict, is_consolidated: bool = False) -> str:
        """Build budget generation prompt"""
        content_type = "información consolidada" if is_consolidated else "términos de referencia"
        
        return f"""
Basándote en la siguiente {content_type} y la información del proyecto, genera un presupuesto detallado.

INFORMACIÓN DEL PROYECTO:
- Título: {project_info.get('title', '')}
- País: {project_info.get('country', '')}
- Duración: {project_info.get('duration_months', '')} meses
- Presupuesto máximo: {project_info.get('budget_cap', 'No especificado')}

{content_type.upper()}:
{content}

Genera un presupuesto detallado con categorías típicas como:
- Personal (salarios, consultores)
- Equipamiento y suministros
- Viajes y transporte
- Capacitación y eventos
- Gastos operativos
- Costos administrativos

Asegúrate de que el presupuesto sea realista y esté dentro del tope especificado.
"""
    
    def _get_budget_schema(self) -> Dict:
        """Get budget schema for JSON generation"""
        return {
            "currency": "USD",
            "items": [
                {
                    "code": "string",
                    "category": "string", 
                    "description": "string",
                    "unit": "string",
                    "qty": "number",
                    "unit_cost": "number",
                    "months": "number",
                    "phase": "string",
                    "justification": "string"
                }
            ],
            "summary_by_category": {},
            "total": "number",
            "assumptions": ["string"],
            "compliance_notes": ["string"]
        }