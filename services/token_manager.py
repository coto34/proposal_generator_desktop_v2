import re
import math
from typing import List, Dict, Any
from dataclasses import dataclass
from datetime import datetime

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
    def get_max_content_tokens(provider: str, prompt_overhead: int = 2000) -> int:
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
        
        # Enhanced section patterns for international development projects
        section_patterns = [
            r'(?i)(?:^|\n)\s*(?:\d+\.?\s*)?(?:background|antecedentes|contexto|situación)',
            r'(?i)(?:^|\n)\s*(?:\d+\.?\s*)?(?:objective|objetivo|propósito|meta)',
            r'(?i)(?:^|\n)\s*(?:\d+\.?\s*)?(?:scope|alcance|ámbito|cobertura)',
            r'(?i)(?:^|\n)\s*(?:\d+\.?\s*)?(?:methodology|metodología|enfoque|estrategia)',
            r'(?i)(?:^|\n)\s*(?:\d+\.?\s*)?(?:activities|actividades|acciones)',
            r'(?i)(?:^|\n)\s*(?:\d+\.?\s*)?(?:deliverable|entregable|producto|resultado)',
            r'(?i)(?:^|\n)\s*(?:\d+\.?\s*)?(?:timeline|cronograma|calendario|duración)',
            r'(?i)(?:^|\n)\s*(?:\d+\.?\s*)?(?:budget|presupuesto|costo|financiamiento)',
            r'(?i)(?:^|\n)\s*(?:\d+\.?\s*)?(?:qualification|calificación|perfil|competencia)',
            r'(?i)(?:^|\n)\s*(?:\d+\.?\s*)?(?:requirement|requisito|condición|criterio)',
            r'(?i)(?:^|\n)\s*(?:\d+\.?\s*)?(?:evaluation|evaluación|selección|valoración)',
            r'(?i)(?:^|\n)\s*(?:\d+\.?\s*)?(?:monitoring|monitoreo|seguimiento|m&e)',
            r'(?i)(?:^|\n)\s*(?:\d+\.?\s*)?(?:sustainability|sostenibilidad|continuidad)',
            r'(?i)(?:^|\n)\s*(?:\d+\.?\s*)?(?:risk|riesgo|contingencia)',
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
    """Handles chained prompts for large documents with IEPADES context"""
    
    def __init__(self, client, max_tokens_per_chunk: int):
        self.client = client
        self.max_tokens_per_chunk = max_tokens_per_chunk
        self.accumulated_context = ""
        self.iepades_context = self._get_iepades_context()
    
    def _get_iepades_context(self) -> str:
        """Get IEPADES organizational context"""
        return """
CONTEXTO ORGANIZACIONAL - IEPADES:
El Instituto de Enseñanza para el Desarrollo Sostenible (IEPADES) es una organización no gubernamental fundada hace más de 30 años en Guatemala, con sólida experiencia en:

ÁREAS DE EXPERTICIA:
• Construcción de paz y prevención de violencia
• Fortalecimiento de capacidades locales y poder local  
• Autogestión comunitaria y participación ciudadana
• Desarrollo sostenible y derechos humanos
• Desarrollo económico local
• Trabajo con pueblos indígenas y comunidades rurales vulnerables

ENFOQUE METODOLÓGICO:
• Participativo y basado en la comunidad
• Sensible al contexto cultural guatemalteco
• Orientado a resultados sostenibles
• Con perspectiva de género e inclusión
• Basado en alianzas estratégicas

EXPERIENCIA GEOGRÁFICA:
• Cobertura nacional en Guatemala
• Experiencia en Centroamérica
• Trabajo especializado en comunidades rurales e indígenas
• Conocimiento profundo del contexto sociopolítico guatemalteco
"""
    
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
                schema = self._get_enhanced_budget_schema()
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
{self.iepades_context}

Analiza este fragmento de los términos de referencia desde la perspectiva de IEPADES y extrae la información clave:

INFORMACIÓN DEL PROYECTO:
- Proyecto: {project_info.get('title', 'N/A')}
- Ubicación: {project_info.get('municipality', 'N/A')}, {project_info.get('department', 'N/A')}, {project_info.get('country', 'Guatemala')}
- Donante: {project_info.get('donor', 'N/A')}
- Duración: {project_info.get('duration_months', 'N/A')} meses

SECCIÓN A ANALIZAR: {chunk['section']}
CONTENIDO:
{chunk['content']}

Extrae y resume considerando la experiencia de IEPADES:
1. Objetivos mencionados (cómo se alinean con la misión de IEPADES)
2. Actividades requeridas (cuáles coinciden con la experticia de IEPADES)
3. Entregables esperados
4. Recursos necesarios
5. Población objetivo y beneficiarios
6. Restricciones o condiciones especiales
7. Información presupuestal (si existe)
8. Consideraciones de sostenibilidad y participación comunitaria

Responde de forma concisa y estructurada, destacando cómo IEPADES puede aportar valor.
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
                schema = self._get_enhanced_budget_schema()
                return self.client.generate_json(final_prompt, schema)
        except Exception as e:
            return f"Error en generación consolidada: {str(e)}"
    
    def _build_narrative_prompt(self, content: str, project_info: Dict, is_consolidated: bool = False) -> str:
        """Build narrative generation prompt with IEPADES context"""
        content_type = "información consolidada" if is_consolidated else "términos de referencia"
        
        # Enhanced location information
        location_details = []
        if project_info.get('department'):
            location_details.append(f"Departamento: {project_info['department']}")
        if project_info.get('municipality'):
            location_details.append(f"Municipio: {project_info['municipality']}")
        if project_info.get('community'):
            location_details.append(f"Comunidad: {project_info['community']}")
        if project_info.get('coverage_type'):
            location_details.append(f"Cobertura: {project_info['coverage_type']}")
        
        location_str = "\n".join(location_details) if location_details else "No especificada"
        
        # Population information
        population_info = []
        if project_info.get('target_population'):
            population_info.append(f"Población objetivo: {project_info['target_population']}")
        if project_info.get('beneficiaries_direct'):
            population_info.append(f"Beneficiarios directos: {project_info['beneficiaries_direct']}")
        if project_info.get('beneficiaries_indirect'):
            population_info.append(f"Beneficiarios indirectos: {project_info['beneficiaries_indirect']}")
        if project_info.get('demographic_focus'):
            population_info.append(f"Enfoque demográfico: {project_info['demographic_focus']}")
        
        population_str = "\n".join(population_info) if population_info else "No especificada"
        
        return f"""
{self.iepades_context}

Basándote en la siguiente {content_type} y información del proyecto, genera una narrativa completa para una propuesta de proyecto en {project_info.get('language', 'es')} que demuestre claramente por qué IEPADES es la organización ideal para ejecutar este proyecto.

INFORMACIÓN DEL PROYECTO:
- Título: {project_info.get('title', '')}
- País: {project_info.get('country', 'Guatemala')}
- Ubicación detallada:
{location_str}
- Donante: {project_info.get('donor', '')}
- Duración: {project_info.get('duration_months', '')} meses
- Presupuesto máximo: {project_info.get('budget_cap', 'No especificado')}

POBLACIÓN OBJETIVO:
{population_str}

PERFIL DE IEPADES (ORGANIZACIÓN EJECUTORA):
{project_info.get('org_profile', '')}

{content_type.upper()}:
{content}

Por favor genera una narrativa completa que incluya:

1. **Resumen Ejecutivo** (destacando la alineación con la misión de IEPADES)
2. **Análisis del Contexto y Justificación** (utilizando el conocimiento de IEPADES sobre Guatemala)
3. **Objetivos y Resultados Esperados** (conectados con la experiencia de IEPADES)
4. **Metodología** (basada en el enfoque participativo de IEPADES)
5. **Plan de Implementación** (aprovechando las fortalezas organizacionales)
6. **Sostenibilidad** (enfocada en el fortalecimiento local, especialidad de IEPADES)
7. **Monitoreo y Evaluación** (con participación comunitaria)
8. **Gestión de Riesgos** (considerando el contexto guatemalteco)

INSTRUCCIONES ESPECÍFICAS:
- La narrativa debe demostrar claramente cómo las 30+ años de experiencia de IEPADES benefician al proyecto
- Incluir referencias específicas a proyectos similares que IEPADES ha ejecutado
- Destacar el conocimiento del contexto sociopolítico guatemalteco
- Enfatizar el enfoque participativo y de fortalecimiento comunitario
- Mostrar sensibilidad cultural, especialmente hacia pueblos indígenas
- Integrar perspectiva de género e inclusión social
- La narrativa debe ser profesional, convincente y técnicamente sólida
- Longitud aproximada: 3,000-4,000 palabras

La narrativa debe posicionar a IEPADES como la opción natural y óptima para la ejecución exitosa del proyecto.
"""
    
    def _build_budget_prompt(self, content: str, project_info: Dict, is_consolidated: bool = False) -> str:
        """Build budget generation prompt with IEPADES context and detailed requirements"""
        content_type = "información consolidada" if is_consolidated else "términos de referencia"
        
        # Enhanced location information for budget
        location_info = f"{project_info.get('municipality', 'N/A')}, {project_info.get('department', 'N/A')}, {project_info.get('country', 'Guatemala')}"
        
        return f"""
{self.iepades_context}

Basándote en la siguiente {content_type} y la información del proyecto, genera un presupuesto extremadamente detallado siguiendo los estándares internacionales más rigurosos para proyectos de desarrollo.

INFORMACIÓN DEL PROYECTO:
- Título: {project_info.get('title', '')}
- Ubicación: {location_info}
- Cobertura: {project_info.get('coverage_type', 'No especificada')}
- Donante: {project_info.get('donor', '')}
- Duración: {project_info.get('duration_months', '')} meses
- Presupuesto máximo: {project_info.get('budget_cap', 'No especificado')}
- Beneficiarios directos: {project_info.get('beneficiaries_direct', 'No especificado')}

{content_type.upper()}:
{content}

REQUERIMIENTOS ESPECÍFICOS DEL PRESUPUESTO:

1. **ESTRUCTURA POR ACTIVIDADES**: Cada ítem presupuestal DEBE estar vinculado a una actividad específica con código (A1.1, A2.1, etc.)

2. **CATEGORÍAS PRINCIPALES** (usar exactamente estos nombres):
   - Personal (incluir salarios de IEPADES y consultores)
   - Equipamiento y Suministros
   - Viajes y Transporte (considerar la ubicación {location_info})
   - Capacitación y Eventos
   - Gastos Operativos
   - Costos Administrativos (máximo 10% del total)
   - Gastos Financieros
   - Contingencias (5-7% del total)

3. **DETALLES OBLIGATORIOS para cada ítem**:
   - Código presupuestal estándar (formato: X.Y.Z)
   - Código de actividad vinculada
   - Descripción técnica detallada
   - Justificación clara y específica
   - Cálculo transparente (cantidad × costo unitario × meses)
   - Fase del proyecto (Inicio/Ejecución/Cierre)
   - Método de adquisición sugerido

4. **CONSIDERACIONES ESPECÍFICAS PARA GUATEMALA**:
   - Costos locales en Quetzales convertidos a USD (usar tasa 7.75)
   - Salarios acordes al mercado guatemalteco
   - Costos de transporte considerando las distancias en {project_info.get('department', 'Guatemala')}
   - Cumplimiento fiscal guatemalteco
   - Consideraciones para trabajo con comunidades indígenas (si aplica)

5. **ANÁLISIS REQUERIDOS**:
   - Resumen por categoría con porcentajes
   - Resumen por actividad
   - Resumen por fase del proyecto
   - Distribución geográfica de costos
   - Análisis de eficiencia (costo por beneficiario)
   - Evaluación de riesgos presupuestales

6. **CUMPLIMIENTO NORMATIVO**:
   - Seguir estándares del donante especificado
   - Incluir notas de cumplimiento
   - Considerar elegibilidad de costos
   - Mecanismos de control y seguimiento

El presupuesto debe reflejar la experiencia y capacidades de IEPADES, ser realista para el contexto guatemalteco, y demostrar eficiencia en el uso de recursos. Incluir al menos 30-50 líneas presupuestales detalladas organizadas por actividades.

IMPORTANTE: Generar un presupuesto que sea técnicamente sólido, detallado y que demuestre profesionalismo en la gestión financiera de proyectos de desarrollo.
"""
    
    def _get_enhanced_budget_schema(self) -> Dict:
        """Get enhanced budget schema for JSON generation with all required fields"""
        return {
            "currency": "USD",
            "exchange_rate": 7.75,
            "items": [
                {
                    "code": "string (formato X.Y.Z)",
                    "activity_code": "string (ej: A1.1)",
                    "activity_name": "string",
                    "category": "string (usar categorías específicas)",
                    "subcategory": "string",
                    "description": "string (descripción detallada)",
                    "unit": "string",
                    "qty": "number",
                    "unit_cost": "number", 
                    "months": "number",
                    "phase": "string (Inicio/Ejecución/Cierre)",
                    "cost_type": "string (Local/Internacional/Mixto)",
                    "justification": "string (justificación técnica)",
                    "procurement_method": "string",
                    "responsible_unit": "string",
                    "donor_eligible": "boolean",
                    "requires_approval": "boolean"
                }
            ],
            "summary_by_category": {"string": "number"},
            "summary_by_activity": [
                {
                    "activity_code": "string",
                    "activity_name": "string", 
                    "total_amount": "number",
                    "percentage_of_total": "number",
                    "main_categories": {"string": "number"}
                }
            ],
            "summary_by_phase": {"string": "number"},
            "summary_by_cost_type": {"string": "number"},
            "geographic_breakdown": [
                {
                    "location": "string",
                    "amount": "number",
                    "percentage": "number",
                    "main_items": ["string"]
                }
            ],
            "subtotal": "number",
            "administrative_cost": "number",
            "administrative_percentage": "number",
            "contingency_amount": "number", 
            "contingency_percentage": "number",
            "total": "number",
            "budget_efficiency_ratio": "number",
            "cost_per_beneficiary": "number",
            "assumptions": ["string"],
            "compliance_notes": [
                {
                    "regulation": "string",
                    "requirement": "string", 
                    "compliance_status": "string",
                    "notes": "string"
                }
            ],
            "risk_assessment": [
                {
                    "risk_category": "string",
                    "risk_description": "string",
                    "probability": "string (Baja/Media/Alta)",
                    "impact": "string (Bajo/Medio/Alto)", 
                    "mitigation_measure": "string",
                    "budget_impact": "number"
                }
            ],
            "monthly_distribution": {"string": "number"},
            "quarterly_milestones": {"string": {"string": "number"}},
            "budget_version": "1.0",
            "preparation_date": datetime.now().strftime("%Y-%m-%d"),
            "prepared_by": "IEPADES",
            "donor_requirements_met": "boolean",
            "eligible_costs_total": "number",
            "non_eligible_costs_total": "number",
            "performance_indicators": [{"indicator": "string", "target": "string", "budget_allocation": "string"}],
            "iepades_expertise_areas": ["string"],
            "environmental_safeguards_cost": "number",
            "social_safeguards_cost": "number", 
            "gender_mainstreaming_cost": "number"
        }