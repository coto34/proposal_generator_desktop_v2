# services/token_manager.py - Enhanced with better chunking and error handling
import re
import math
import logging
from typing import List, Dict, Any, Optional, Callable
from dataclasses import dataclass
from datetime import datetime
import hashlib


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class TokenLimits:
    DEEPSEEK_CONTEXT = 32000  # DeepSeek context window
    SONNET_CONTEXT = 200000   # Claude Sonnet context window
    SAFETY_MARGIN = 0.75      # Use 75% of context to be conservative
    AVG_CHARS_PER_TOKEN = 4   # Conservative estimate: 1 token ≈ 4 characters
    MIN_CHUNK_SIZE = 500      # Minimum characters per chunk
    MAX_OVERLAP = 200         # Maximum overlap between chunks


class TokenManager:
    """Enhanced token manager with intelligent chunking strategies"""

    @staticmethod
    def estimate_tokens(text: str) -> int:
        """More accurate token estimation"""
        if not text:
            return 0

        # More sophisticated token counting
        # Account for special characters, whitespace, etc.
        words = len(text.split())
        chars = len(text)

        # Heuristic: combine word count and character count
        estimated = max(words * 1.3, chars / TokenLimits.AVG_CHARS_PER_TOKEN)
        return int(estimated)

    @staticmethod
    def get_max_content_tokens(provider: str, prompt_overhead: int = 2500) -> int:
        """Get maximum tokens available for content with dynamic overhead calculation"""
        provider_limits = {
            "deepseek": TokenLimits.DEEPSEEK_CONTEXT,
            "sonnet": TokenLimits.SONNET_CONTEXT,
            "claude": TokenLimits.SONNET_CONTEXT,  # Alias
            "anthropic": TokenLimits.SONNET_CONTEXT  # Alias
        }

        total_limit = provider_limits.get(provider.lower(), 8000)  # Default
        available = int(total_limit * TokenLimits.SAFETY_MARGIN)

        # Dynamic prompt overhead based on provider
        if provider.lower() == "deepseek":
            prompt_overhead = min(prompt_overhead, 3000)  # Cap overhead for DeepSeek

        return max(available - prompt_overhead, 1000)  # Minimum 1000 tokens

    @staticmethod
    def intelligent_chunk_tor(tor_content: str, max_tokens_per_chunk: int,
                             overlap_tokens: int = 100) -> List[Dict[str, Any]]:
        """
        Enhanced intelligent chunking with better section detection and overlap
        """
        if not tor_content or not tor_content.strip():
            return []

        # Quick check - if content fits in one chunk, return as-is
        estimated_tokens = TokenManager.estimate_tokens(tor_content)
        if estimated_tokens <= max_tokens_per_chunk:
            return [{
                "content": tor_content.strip(),
                "section": "complete",
                "index": 0,
                "tokens_estimated": estimated_tokens,
                "chunk_id": TokenManager._generate_chunk_id(tor_content)
            }]

        logger.info(f"Chunking document: {estimated_tokens} tokens into {max_tokens_per_chunk} token chunks")

        # Try hierarchical chunking
        chunks = TokenManager._hierarchical_chunk(tor_content, max_tokens_per_chunk, overlap_tokens)

        if not chunks:
            # Fallback to simple paragraph chunking
            chunks = TokenManager._paragraph_chunk(tor_content, max_tokens_per_chunk, overlap_tokens)

        if not chunks:
            # Final fallback to character chunking
            chunks = TokenManager._character_chunk(tor_content, max_tokens_per_chunk, overlap_tokens)

        # Post-process chunks
        return TokenManager._post_process_chunks(chunks)

    @staticmethod
    def _hierarchical_chunk(content: str, max_tokens: int, overlap_tokens: int) -> List[Dict[str, Any]]:
        """
        Hierarchical chunking: sections -> subsections -> paragraphs
        """
        try:
            # Level 1: Major sections
            sections = TokenManager._split_by_major_sections(content)

            if len(sections) <= 1:
                # No clear sections, try subsections
                sections = TokenManager._split_by_subsections(content)

            chunks = []
            section_overlap = ""

            for i, section in enumerate(sections):
                section_tokens = TokenManager.estimate_tokens(section['content'])

                if section_tokens <= max_tokens:
                    # Section fits in one chunk
                    chunk_content = section_overlap + section['content']
                    if TokenManager.estimate_tokens(chunk_content) <= max_tokens:
                        chunks.append({
                            "content": chunk_content.strip(),
                            "section": section['section'],
                            "index": i,
                            "tokens_estimated": TokenManager.estimate_tokens(chunk_content)
                        })

                        # Prepare overlap for next chunk
                        section_overlap = TokenManager._create_overlap(section['content'], overlap_tokens)
                    else:
                        # Add previous chunk without overlap
                        chunks.append(section)
                        section_overlap = TokenManager._create_overlap(section['content'], overlap_tokens)
                else:
                    # Section too large, split further
                    sub_chunks = TokenManager._split_large_section(
                        section, max_tokens, overlap_tokens
                    )
                    chunks.extend(sub_chunks)

                    if sub_chunks:
                        section_overlap = TokenManager._create_overlap(
                            sub_chunks[-1]['content'], overlap_tokens
                        )

            return chunks

        except Exception as e:
            logger.error(f"Error in hierarchical chunking: {e}")
            return []

    @staticmethod
    def _split_by_major_sections(content: str) -> List[Dict[str, str]]:
        """Split by major ToR sections with enhanced patterns"""

        # Enhanced section patterns for international development
        major_section_patterns = [
            # English patterns
            r'(?i)(?:^|\n)\s*(?:\d+\.?\s*)?(?:background|context|overview|introduction)',
            r'(?i)(?:^|\n)\s*(?:\d+\.?\s*)?(?:objective|purpose|goal|aim)s?',
            r'(?i)(?:^|\n)\s*(?:\d+\.?\s*)?(?:scope|coverage|geographical)',
            r'(?i)(?:^|\n)\s*(?:\d+\.?\s*)?(?:methodology|approach|implementation)',
            r'(?i)(?:^|\n)\s*(?:\d+\.?\s*)?(?:activities|tasks|work|deliverable)',
            r'(?i)(?:^|\n)\s*(?:\d+\.?\s*)?(?:timeline|schedule|duration|timeframe)',
            r'(?i)(?:^|\n)\s*(?:\d+\.?\s*)?(?:budget|financial|cost|funding)',
            r'(?i)(?:^|\n)\s*(?:\d+\.?\s*)?(?:qualification|requirement|competenc|skill)',
            r'(?i)(?:^|\n)\s*(?:\d+\.?\s*)?(?:evaluation|assessment|selection)',
            r'(?i)(?:^|\n)\s*(?:\d+\.?\s*)?(?:monitoring|reporting|m&e)',
            r'(?i)(?:^|\n)\s*(?:\d+\.?\s*)?(?:sustainability|impact|outcome)',
            r'(?i)(?:^|\n)\s*(?:\d+\.?\s*)?(?:risk|assumption|constraint)',

            # Spanish patterns
            r'(?i)(?:^|\n)\s*(?:\d+\.?\s*)?(?:antecedentes|contexto|introducción)',
            r'(?i)(?:^|\n)\s*(?:\d+\.?\s*)?(?:objetivo|propósito|meta|finalidad)',
            r'(?i)(?:^|\n)\s*(?:\d+\.?\s*)?(?:alcance|cobertura|ámbito)',
            r'(?i)(?:^|\n)\s*(?:\d+\.?\s*)?(?:metodología|enfoque|implementación)',
            r'(?i)(?:^|\n)\s*(?:\d+\.?\s*)?(?:actividades|tareas|trabajo|entregable)',
            r'(?i)(?:^|\n)\s*(?:\d+\.?\s*)?(?:cronograma|calendario|duración)',
            r'(?i)(?:^|\n)\s*(?:\d+\.?\s*)?(?:presupuesto|financiamiento|costo)',
            r'(?i)(?:^|\n)\s*(?:\d+\.?\s*)?(?:calificación|requisito|competencia)',
            r'(?i)(?:^|\n)\s*(?:\d+\.?\s*)?(?:evaluación|selección|valoración)',
            r'(?i)(?:^|\n)\s*(?:\d+\.?\s*)?(?:monitoreo|seguimiento|reporte)',
            r'(?i)(?:^|\n)\s*(?:\d+\.?\s*)?(?:sostenibilidad|impacto|resultado)',
            r'(?i)(?:^|\n)\s*(?:\d+\.?\s*)?(?:riesgo|supuesto|limitación)'
        ]

        # Find section breaks
        section_breaks = []
        for pattern in major_section_patterns:
            for match in re.finditer(pattern, content):
                section_name = TokenManager._extract_section_name(match.group())
                section_breaks.append((match.start(), section_name, match.group()))

        # Sort by position and remove duplicates
        section_breaks.sort()
        unique_breaks = []
        for i, (pos, name, text) in enumerate(section_breaks):
            if i == 0 or pos - unique_breaks[-1][0] > 50:  # Minimum 50 chars between sections
                unique_breaks.append((pos, name, text))

        if len(unique_breaks) < 2:
            return []  # Not enough sections found

        # Create sections
        sections = []
        for i, (start_pos, section_name, _) in enumerate(unique_breaks):
            end_pos = unique_breaks[i + 1][0] if i + 1 < len(unique_breaks) else len(content)

            section_content = content[start_pos:end_pos].strip()
            if len(section_content) > TokenLimits.MIN_CHUNK_SIZE:
                sections.append({
                    "content": section_content,
                    "section": section_name,
                    "start_pos": start_pos,
                    "end_pos": end_pos
                })

        return sections

    @staticmethod
    def _split_by_subsections(content: str) -> List[Dict[str, str]]:
        """Split by subsections when major sections aren't found"""

        subsection_patterns = [
            r'(?i)(?:^|\n)\s*(?:\d+\.\d+\.?\s*)(?:[A-Za-z])',  # 1.1, 2.3, etc.
            r'(?i)(?:^|\n)\s*(?:[a-z]\)\s*)(?:[A-Za-z])',      # a), b), etc.
            r'(?i)(?:^|\n)\s*(?:[ivxlc]+\.\s*)(?:[A-Za-z])',   # i., ii., etc.
            r'(?i)(?:^|\n)\s*(?:•|\*|-|\+)\s*(?:[A-Za-z])',    # Bullet points
            r'(?i)(?:^|\n)\s*(?:\d+\.?\s*[A-Z])',            # 1. Capital letter start
        ]

        breaks = []
        for pattern in subsection_patterns:
            for match in re.finditer(pattern, content):
                section_name = f"subsection_{len(breaks)}"
                breaks.append((match.start(), section_name))

        breaks.sort()

        if len(breaks) < 2:
            return []

        sections = []
        for i, (start_pos, section_name) in enumerate(breaks):
            end_pos = breaks[i + 1][0] if i + 1 < len(breaks) else len(content)
            section_content = content[start_pos:end_pos].strip()

            if len(section_content) > TokenLimits.MIN_CHUNK_SIZE:
                sections.append({
                    "content": section_content,
                    "section": section_name
                })

        return sections

    @staticmethod
    def _split_large_section(section: Dict, max_tokens: int, overlap_tokens: int) -> List[Dict[str, Any]]:
        """Split a large section into smaller chunks"""
        content = section['content']
        section_name = section['section']

        # Try paragraph-based splitting first
        paragraphs = [p.strip() for p in content.split('\n\n') if p.strip()]

        chunks = []
        current_chunk = ""
        current_tokens = 0

        for para in paragraphs:
            para_tokens = TokenManager.estimate_tokens(para)

            # If paragraph itself is too large, split it
            if para_tokens > max_tokens:
                # Save current chunk if it has content
                if current_chunk:
                    chunks.append({
                        "content": current_chunk.strip(),
                        "section": f"{section_name}_part_{len(chunks)}",
                        "tokens_estimated": current_tokens
                    })
                    current_chunk = ""
                    current_tokens = 0

                # Split the large paragraph
                para_chunks = TokenManager._split_large_paragraph(para, max_tokens, section_name)
                chunks.extend(para_chunks)

            elif current_tokens + para_tokens <= max_tokens:
                # Add paragraph to current chunk
                if current_chunk:
                    current_chunk += "\n\n" + para
                else:
                    current_chunk = para
                current_tokens += para_tokens

            else:
                # Save current chunk and start new one
                if current_chunk:
                    chunks.append({
                        "content": current_chunk.strip(),
                        "section": f"{section_name}_part_{len(chunks)}",
                        "tokens_estimated": current_tokens
                    })

                current_chunk = para
                current_tokens = para_tokens

        # Add final chunk
        if current_chunk:
            chunks.append({
                "content": current_chunk.strip(),
                "section": f"{section_name}_part_{len(chunks)}",
                "tokens_estimated": current_tokens
            })

        return chunks

    @staticmethod
    def _split_large_paragraph(paragraph: str, max_tokens: int, section_name: str) -> List[Dict[str, Any]]:
        """Split a large paragraph by sentences"""
        sentences = re.split(r'(?<=[.!?])\s+', paragraph)

        chunks = []
        current_chunk = ""
        current_tokens = 0

        for sentence in sentences:
            sentence_tokens = TokenManager.estimate_tokens(sentence)

            if current_tokens + sentence_tokens <= max_tokens:
                if current_chunk:
                    current_chunk += " " + sentence
                else:
                    current_chunk = sentence
                current_tokens += sentence_tokens
            else:
                if current_chunk:
                    chunks.append({
                        "content": current_chunk.strip(),
                        "section": f"{section_name}_sentence_{len(chunks)}",
                        "tokens_estimated": current_tokens
                    })

                # If single sentence is too long, truncate or split by characters
                if sentence_tokens > max_tokens:
                    char_chunks = TokenManager._character_chunk_text(sentence, max_tokens)
                    chunks.extend([{
                        "content": chunk,
                        "section": f"{section_name}_char_{i}",
                        "tokens_estimated": TokenManager.estimate_tokens(chunk)
                    } for i, chunk in enumerate(char_chunks)])
                    current_chunk = ""
                    current_tokens = 0
                else:
                    current_chunk = sentence
                    current_tokens = sentence_tokens

        if current_chunk:
            chunks.append({
                "content": current_chunk.strip(),
                "section": f"{section_name}_sentence_{len(chunks)}",
                "tokens_estimated": current_tokens
            })

        return chunks

    @staticmethod
    def _paragraph_chunk(content: str, max_tokens: int, overlap_tokens: int) -> List[Dict[str, Any]]:
        """Fallback paragraph-based chunking"""
        paragraphs = [p.strip() for p in content.split('\n\n') if p.strip()]

        chunks = []
        current_chunk = ""
        current_tokens = 0

        for para in paragraphs:
            para_tokens = TokenManager.estimate_tokens(para)

            if current_tokens + para_tokens <= max_tokens:
                if current_chunk:
                    current_chunk += "\n\n" + para
                else:
                    current_chunk = para
                current_tokens += para_tokens
            else:
                if current_chunk:
                    chunks.append({
                        "content": current_chunk.strip(),
                        "section": f"paragraph_chunk_{len(chunks)}",
                        "tokens_estimated": current_tokens
                    })

                current_chunk = para
                current_tokens = para_tokens

        if current_chunk:
            chunks.append({
                "content": current_chunk.strip(),
                "section": f"paragraph_chunk_{len(chunks)}",
                "tokens_estimated": current_tokens
            })

        return chunks

    @staticmethod
    def _character_chunk(content: str, max_tokens: int, overlap_tokens: int) -> List[Dict[str, Any]]:
        """Final fallback: character-based chunking"""
        max_chars = max_tokens * TokenLimits.AVG_CHARS_PER_TOKEN
        overlap_chars = overlap_tokens * TokenLimits.AVG_CHARS_PER_TOKEN

        chunks = []
        start = 0
        chunk_index = 0

        while start < len(content):
            end = min(start + max_chars, len(content))

            # Try to break at word boundary
            if end < len(content):
                # Look for nearest word boundary
                for i in range(end, max(start, end - 100), -1):
                    if content[i].isspace():
                        end = i
                        break

            chunk_content = content[start:end].strip()
            if chunk_content:
                chunks.append({
                    "content": chunk_content,
                    "section": f"char_chunk_{chunk_index}",
                    "tokens_estimated": TokenManager.estimate_tokens(chunk_content)
                })
                chunk_index += 1

            # Move start position with overlap
            start = max(end - overlap_chars, start + 1)

            # Prevent infinite loop
            if start >= end:
                break

        return chunks

    @staticmethod
    def _character_chunk_text(text: str, max_tokens: int) -> List[str]:
        """Split text by characters with word boundary consideration"""
        max_chars = max_tokens * TokenLimits.AVG_CHARS_PER_TOKEN

        chunks = []
        start = 0

        while start < len(text):
            end = min(start + max_chars, len(text))

            # Try to break at word boundary
            # Try to break at word boundary
            if end < len(text):
                for i in range(end, max(start, end - 100), -1):
                    if text[i].isspace():
                        end = i
                        break

            chunk = text[start:end].strip()
            if chunk:
                chunks.append(chunk)

            start = end
            if start >= len(text):
                break

        return chunks

    @staticmethod
    def _create_overlap(content: str, overlap_tokens: int) -> str:
        """Create overlap text from the end of content"""
        if overlap_tokens <= 0:
            return ""

        sentences = re.split(r'(?<=[.!?])\s+', content)
        overlap_content = ""
        current_tokens = 0

        # Take sentences from the end
        for sentence in reversed(sentences):
            sentence_tokens = TokenManager.estimate_tokens(sentence)
            if current_tokens + sentence_tokens <= overlap_tokens:
                if overlap_content:
                    overlap_content = sentence + " " + overlap_content
                else:
                    overlap_content = sentence
                current_tokens += sentence_tokens
            else:
                break

        return overlap_content + "\n\n" if overlap_content else ""

    @staticmethod
    def _post_process_chunks(chunks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Post-process chunks with additional metadata"""
        processed_chunks = []

        for i, chunk in enumerate(chunks):
            # Add additional metadata
            chunk_data = {
                **chunk,
                "index": i,
                "chunk_id": TokenManager._generate_chunk_id(chunk.get("content", "")),
                "word_count": len(chunk.get("content", "").split()),
                "char_count": len(chunk.get("content", "")),
                "processed_at": datetime.now().isoformat()
            }

            # Validate chunk
            if TokenManager._validate_chunk(chunk_data):
                processed_chunks.append(chunk_data)
            else:
                logger.warning(f"Invalid chunk {i} filtered out")

        return processed_chunks

    @staticmethod
    def _validate_chunk(chunk: Dict[str, Any]) -> bool:
        """Validate chunk quality"""
        content = chunk.get("content", "")

        # Minimum content length
        if len(content.strip()) < 50:
            return False

        # Check for reasonable token estimate
        estimated_tokens = chunk.get("tokens_estimated", 0)
        if estimated_tokens <= 0:
            return False

        # Check content isn't just whitespace or special characters
        if not re.search(r'[A-Za-z0-9]', content):
            return False

        return True

    @staticmethod
    def _generate_chunk_id(content: str) -> str:
        """Generate unique ID for chunk"""
        return hashlib.md5(content.encode('utf-8')).hexdigest()[:8]

    @staticmethod
    def _extract_section_name(header: str) -> str:
        """Extract clean section name from header"""
        # Remove numbers and special chars
        clean = re.sub(r'^\s*\d+\.?\s*', '', header.strip())
        clean = re.sub(r'[^\w\s]', '', clean)
        clean = re.sub(r'\s+', '_', clean.lower())
        return clean[:30] if clean else f"section_{hash(header) % 1000}"


class EnhancedChainedPromptGenerator:
    """Enhanced chained prompt generator with better context management"""

    def __init__(self, client, max_tokens_per_chunk: int, progress_callback: Optional[Callable[[str], None]] = None):
        self.client = client
        self.max_tokens_per_chunk = max_tokens_per_chunk
        self.progress_callback = progress_callback or (lambda x: None)
        self.accumulated_context = ""
        self.processing_stats = {
            "chunks_processed": 0,
            "total_tokens_processed": 0,
            "processing_time": 0,
            "errors": []
        }
        self.iepades_context = self._get_enhanced_iepades_context()

    def _get_enhanced_iepades_context(self) -> str:
        """Enhanced IEPADES context with more detail"""
        return """
PERFIL INSTITUCIONAL DETALLADO - IEPADES
========================================

INFORMACIÓN BÁSICA:
Nombre: Instituto de Enseñanza para el Desarrollo Sostenible (IEPADES)
Fundación: Más de 30 años de experiencia en Guatemala
Tipo: Organización No Gubernamental (ONG)
Estatus: Legalmente constituida, con personería jurídica vigente

MISIÓN Y VISIÓN:
Misión: Promover la paz, la democracia y el desarrollo sostenible mediante el fortalecimiento
del poder local y la participación ciudadana, especialmente en comunidades rurales y vulnerables.

Visión: Una Guatemala donde las comunidades ejercen plenamente sus derechos, participan
activamente en la toma de decisiones y construyen un desarrollo sostenible y equitativo.

ÁREAS DE EXPERTISE TÉCNICA:
• Construcción de paz y prevención de violencia comunitaria
• Fortalecimiento de capacidades locales y poder local
• Autogestión comunitaria y desarrollo participativo
• Desarrollo sostenible con enfoque territorial
• Derechos humanos y justicia social
• Participación ciudadana y democracia local
• Desarrollo económico local y emprendimiento
• Gestión de recursos naturales
• Adaptación y mitigación del cambio climático
• Seguridad alimentaria y nutricional

EXPERIENCIA GEOGRÁFICA Y CULTURAL:
• Cobertura nacional en Guatemala con presencia territorial consolidada
• Experiencia en los 22 departamentos guatemaltecos
• Trabajo especializado con pueblos indígenas (Maya, Garífuna, Xinka)
• Conocimiento profundo del contexto sociopolítico guatemalteco
• Experiencia en zonas rurales remotas y de difícil acceso
• Trabajo en contextos post-conflicto y de alta vulnerabilidad

CAPACIDADES INSTITUCIONALES:
• Equipo multidisciplinario con experiencia probada
• Red de facilitadores comunitarios a nivel nacional
• Alianzas estratégicas con organizaciones locales e internacionales
• Sistemas de monitoreo y evaluación participativa
• Capacidad de gestión financiera transparente y eficiente
• Experiencia en gestión de proyectos con múltiples donantes

ENFOQUE METODOLÓGICO:
• Metodología participativa basada en la comunidad
• Enfoque de derechos humanos y género
• Interculturalidad y pertinencia cultural
• Sostenibilidad y apropiación local
• Construcción de alianzas y trabajo en red
• Diálogo y construcción de consensos

DONANTES Y SOCIOS ESTRATÉGICOS:
Experiencia con organismos internacionales, embajadas, fundaciones privadas,
y agencias de cooperación bilateral y multilateral.
"""

    def process_tor_chunks(self, chunks: List[Dict[str, Any]], project_info: Dict,
                           task_type: str, max_retries: int = 3) -> Any:
        """Enhanced chunk processing with retries and better error handling"""

        if not chunks:
            error_msg = f"No hay chunks disponibles para procesar ({task_type})"
            self.processing_stats["errors"].append(error_msg)
            return self._get_error_result(task_type, error_msg)

        start_time = datetime.now()

        try:
            self.progress_callback(f"Procesando {len(chunks)} chunk(s) para {task_type}")

            if len(chunks) == 1:
                # Single chunk processing
                result = self._process_single_chunk_with_retries(
                    chunks[0], project_info, task_type, max_retries
                )
            else:
                # Multi-chunk processing with context chaining
                result = self._process_multiple_chunks_with_context(
                    chunks, project_info, task_type, max_retries
                )

            # Update stats
            processing_time = (datetime.now() - start_time).total_seconds()
            self.processing_stats.update({
                "chunks_processed": len(chunks),
                "total_tokens_processed": sum(c.get("tokens_estimated", 0) for c in chunks),
                "processing_time": processing_time
            })

            self.progress_callback(f"Procesamiento completado en {processing_time:.1f}s")

            return result

        except Exception as e:
            error_msg = f"Error crítico en procesamiento: {str(e)}"
            logger.exception(error_msg)
            self.processing_stats["errors"].append(error_msg)
            return self._get_error_result(task_type, error_msg)

    def _process_single_chunk_with_retries(self, chunk: Dict[str, Any], project_info: Dict,
                                          task_type: str, max_retries: int) -> Any:
        """Process single chunk with retry logic"""

        for attempt in range(max_retries):
            try:
                self.progress_callback(f"Procesando chunk único (intento {attempt + 1})")

                if task_type == "narrative":
                    prompt = self._build_enhanced_narrative_prompt(chunk["content"], project_info)
                    result = self.client.generate(prompt, self.progress_callback)
                    return result.content if hasattr(result, 'content') else result
                else:
                    prompt = self._build_enhanced_budget_prompt(chunk["content"], project_info)
                    schema = self._get_comprehensive_budget_schema()
                    return self.client.generate_json(prompt, schema, self.progress_callback)

            except Exception as e:
                error_msg = f"Error en intento {attempt + 1}: {str(e)}"
                logger.warning(error_msg)

                if attempt == max_retries - 1:
                    return self._get_error_result(task_type, f"Falló después de {max_retries} intentos: {str(e)}")

                # Wait before retry
                import time
                time.sleep(2 ** attempt)  # Exponential backoff

        return self._get_error_result(task_type, "Máximo número de reintentos alcanzado")

    def _process_multiple_chunks_with_context(self, chunks: List[Dict[str, Any]],
                                             project_info: Dict, task_type: str, max_retries: int) -> Any:
        """Process multiple chunks with context chaining"""

        self.progress_callback("Iniciando procesamiento encadenado de chunks")

        # Phase 1: Extract key information from each chunk
        chunk_summaries = []
        for i, chunk in enumerate(chunks):
            try:
                self.progress_callback(f"Analizando chunk {i+1}/{len(chunks)}: {chunk['section']}")

                summary = self._extract_chunk_information(chunk, project_info, task_type)
                if summary:
                    chunk_summaries.append(summary)

            except Exception as e:
                logger.warning(f"Error procesando chunk {i}: {str(e)}")
                chunk_summaries.append(f"Error en chunk {chunk['section']}: {str(e)}")

        # Phase 2: Synthesize information
        if not chunk_summaries:
            return self._get_error_result(task_type, "No se pudo extraer información de ningún chunk")

        consolidated_info = "\n\n".join(chunk_summaries)

        try:
            self.progress_callback("Sintetizando información consolidada")

            if task_type == "narrative":
                final_prompt = self._build_enhanced_narrative_prompt(
                    consolidated_info, project_info, is_consolidated=True
                )
                result = self.client.generate(final_prompt, self.progress_callback)
            else:
                final_prompt = self._build_enhanced_budget_prompt(
                    consolidated_info, project_info, is_consolidated=True
                )
                schema = self._get_comprehensive_budget_schema()
                result = self.client.generate_json(final_prompt, schema, self.progress_callback)

            return result.content if hasattr(result, 'content') else result
        except Exception as e:
            return self._get_error_result(task_type, f"Error en síntesis final: {str(e)}")

    def _extract_chunk_information(self, chunk: Dict[str, Any], project_info: Dict,
                                   task_type: str) -> Optional[str]:
        """Extract key information from a chunk"""

        extraction_prompt = f"""
{self.iepades_context}

ANÁLISIS DE FRAGMENTO DE TÉRMINOS DE REFERENCIA

Información del proyecto:
- Título: {project_info.get('title', 'N/A')}
- País: {project_info.get('country', 'Guatemala')}
- Ubicación: {project_info.get('municipality', '')}, {project_info.get('department', '')}
- Donante: {project_info.get('donor', 'N/A')}
- Duración: {project_info.get('duration_months', 'N/A')} meses
- Presupuesto máximo: {project_info.get('budget_cap', 'No especificado')}

FRAGMENTO A ANALIZAR (Sección: {chunk['section']}):
{chunk['content']}

INSTRUCCIONES:
Analiza este fragmento desde la perspectiva de IEPADES y extrae información clave relevante para {'la narrativa del proyecto' if task_type == 'narrative' else 'la elaboración del presupuesto'}:

1. Objetivos específicos mencionados
2. Actividades y metodologías requeridas
3. Entregables y productos esperados
4. Recursos humanos y técnicos necesarios
5. Consideraciones presupuestales (si aplica)
6. Población objetivo y beneficiarios
7. Ubicación geográfica y contexto
8. Cronograma o plazos mencionados
9. Requisitos específicos del donante
10. Oportunidades para aplicar la experiencia de IEPADES

Responde de forma estructurada y concisa, enfocándote en elementos que IEPADES puede aportar basado en su experiencia de 30+ años en Guatemala.
"""

        try:
            if hasattr(self.client, 'generate'):
                result = self.client.generate(extraction_prompt)
                return f"ANÁLISIS - {chunk['section']}:\n{result.content if hasattr(result, 'content') else result}\n"
            else:
                # For budget clients, return simplified extraction
                return f"SECCIÓN - {chunk['section']}:\n{chunk['content'][:800]}...\n"

        except Exception as e:
            logger.warning(f"Error extrayendo información de chunk: {str(e)}")
            return f"ERROR - {chunk['section']}: No se pudo procesar\n"

    def _build_enhanced_narrative_prompt(self, content: str, project_info: Dict,
                                        is_consolidated: bool = False) -> str:
        """Build comprehensive narrative prompt"""

        content_type = "información consolidada de múltiples secciones" if is_consolidated else "términos de referencia"

        # Enhanced project location information
        location_details = []
        if project_info.get('coverage_type'):
            location_details.append(f"Cobertura: {project_info['coverage_type']}")
        if project_info.get('department'):
            location_details.append(f"Departamento: {project_info['department']}")
        if project_info.get('municipality'):
            location_details.append(f"Municipio: {project_info['municipality']}")
        if project_info.get('community'):
            location_details.append(f"Comunidad/Aldea: {project_info['community']}")

        location_str = " | ".join(location_details) if location_details else "Guatemala (ubicación por definir)"

        # Population and beneficiaries
        population_details = []
        if project_info.get('target_population'):
            population_details.append(f"Población objetivo: {project_info['target_population'][:200]}...")
        if project_info.get('beneficiaries_direct'):
            population_details.append(f"Beneficiarios directos: {project_info['beneficiaries_direct']}")
        if project_info.get('beneficiaries_indirect'):
            population_details.append(f"Beneficiarios indirectos: {project_info['beneficiaries_indirect']}")
        if project_info.get('demographic_focus'):
            population_details.append(f"Enfoque demográfico: {project_info['demographic_focus']}")

        population_str = "\n".join(population_details) if population_details else "Por definir según ToR"

        return f"""
{self.iepades_context}

GENERACIÓN DE NARRATIVA COMPLETA DE PROPUESTA

Basándote en la siguiente {content_type} y la información del proyecto, genera una narrativa integral y convincente que posicione a IEPADES como la organización ideal para ejecutar este proyecto.

INFORMACIÓN DETALLADA DEL PROYECTO:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Título: {project_info.get('title', 'Proyecto de Desarrollo')}
País: {project_info.get('country', 'Guatemala')}
Ubicación específica: {location_str}
Donante/Financiador: {project_info.get('donor', 'Por definir')}
Duración del proyecto: {project_info.get('duration_months', 'N/A')} meses
Presupuesto referencial: {project_info.get('budget_cap', 'A determinar según propuesta')}
Idioma de la propuesta: {project_info.get('language', 'Español')}

POBLACIÓN OBJETIVO Y BENEFICIARIOS:
{population_str}

PERFIL DETALLADO DE IEPADES:
{project_info.get('org_profile', 'Ver contexto institucional arriba')}

{content_type.upper()}:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
{content}

ESTRUCTURA REQUERIDA PARA LA NARRATIVA:

1. **RESUMEN EJECUTIVO** (400-500 palabras)
   - Síntesis del proyecto y su relevancia
   - Valor agregado único que aporta IEPADES
   - Resultados esperados e impacto proyectado

2. **ANÁLISIS DEL CONTEXTO Y JUSTIFICACIÓN** (600-800 palabras)
   - Diagnóstico de la situación actual
   - Problemática que aborda el proyecto
   - Oportunidades identificadas
   - Alineación con prioridades nacionales/locales

3. **OBJETIVOS Y RESULTADOS ESPERADOS** (500-600 palabras)
   - Objetivo general y objetivos específicos
   - Resultados esperados por componente
   - Indicadores de éxito cualitativos y cuantitativos
   - Teoría de cambio implícita

4. **ESTRATEGIA METODOLÓGICA** (700-900 palabras)
   - Enfoque metodológico de IEPADES
   - Estrategias de implementación participativa
   - Mecanismos de apropiación comunitaria
   - Innovaciones metodológicas propuestas

5. **PLAN DE IMPLEMENTACIÓN** (600-800 palabras)
   - Fases del proyecto y cronograma general
   - Actividades clave por componente
   - Recursos humanos y técnicos requeridos
   - Estrategia de articulación territorial

6. **SOSTENIBILIDAD E IMPACTO** (500-600 palabras)
   - Mecanismos de sostenibilidad propuestos
   - Estrategias de fortalecimiento institucional
   - Impacto esperado a mediano y largo plazo
   - Replicabilidad y escalabilidad

7. **MONITOREO, EVALUACIÓN Y APRENDIZAJE** (400-500 palabras)
   - Sistema de monitoreo participativo
   - Momentos de evaluación programados
   - Mecanismos de retroalimentación
   - Gestión del conocimiento y lecciones aprendidas

8. **GESTIÓN DE RIESGOS Y MEDIDAS DE MITIGACIÓN** (400-500 palabras)
   - Identificación de riesgos principales
   - Medidas preventivas y de mitigación
   - Plan de contingencia
   - Mecanismos de alerta temprana

CRITERIOS DE CALIDAD PARA LA NARRATIVA:

✓ **PERTINENCIA**: Demuestra comprensión profunda del contexto guatemalteco
✓ **EXPERIENCIA**: Integra casos exitosos y lecciones aprendidas de IEPADES
✓ **INNOVACIÓN**: Propone enfoques creativos basados en buenas prácticas
✓ **PARTICIPACIÓN**: Enfatiza metodologías participativas e inclusivas
✓ **SOSTENIBILIDAD**: Prioriza apropiación local y continuidad de procesos
✓ **EFICIENCIA**: Optimiza recursos y maximiza impacto
✓ **TRANSPARENCIA**: Incluye mecanismos de rendición de cuentas
✓ **COHERENCIA**: Mantiene consistencia entre objetivos, metodología y resultados

INSTRUCCIONES ESPECÍFICAS:
• La narrativa debe ser técnicamente sólida y profesional
• Usar terminología apropiada para el sector de desarrollo internacional
• Incorporar referencias específicas a la experiencia de IEPADES cuando sea relevante
• Demostrar conocimiento del contexto político, social y económico guatemalteco
• Evidenciar capacidad de trabajo con pueblos indígenas y comunidades rurales
• Incluir consideraciones de género, interculturalidad e inclusión social
• Mantener un tono convincente pero no exagerado
• Asegurar coherencia entre todas las secciones

LONGITUD OBJETIVO: 4,000-5,000 palabras (narrativa completa y detallada)

La narrativa debe posicionar convincentemente a IEPADES como la organización con mayor capacidad técnica, experiencia contextual y compromiso ético para ejecutar exitosamente este proyecto, maximizando su impacto en la población beneficiaria.
"""

    def _build_enhanced_budget_prompt(self, content: str, project_info: Dict,
                                     is_consolidated: bool = False) -> str:
        """Build comprehensive budget prompt"""

        content_type = "información consolidada de múltiples secciones" if is_consolidated else "términos de referencia"
        location_info = f"{project_info.get('municipality', 'N/A')}, {project_info.get('department', 'N/A')}, {project_info.get('country', 'Guatemala')}"

        return f"""
{self.iepades_context}

GENERACIÓN DE PRESUPUESTO INTEGRAL Y DETALLADO

Basándote en la siguiente {content_type} y la información del proyecto, elabora un presupuesto extremadamente detallado que cumpla con los más altos estándares internacionales para proyectos de desarrollo y demuestre la capacidad de gestión financiera profesional de IEPADES.

INFORMACIÓN DETALLADA DEL PROYECTO:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
• Título: {project_info.get('title', 'Proyecto de Desarrollo')}
• Ubicación específica: {location_info}
• Cobertura geográfica: {project_info.get('coverage_type', 'Local')}
• Donante/Financiador: {project_info.get('donor', 'Por definir')}
• Duración total: {project_info.get('duration_months', 'N/A')} meses
• Presupuesto máximo: {project_info.get('budget_cap', 'Por determinar')}
• Beneficiarios directos: {project_info.get('beneficiaries_direct', 'Por definir')}
• Enfoque demográfico: {project_info.get('demographic_focus', 'Población general')}

{content_type.upper()}:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
{content}

REQUERIMIENTOS ESPECÍFICOS DEL PRESUPUESTO:

🏗️ **ESTRUCTURA ORGANIZACIONAL OBLIGATORIA**
El presupuesto DEBE organizarse por actividades específicas con códigos claros:
- A1.1, A1.2, A1.3... (Actividades del Componente 1)
- A2.1, A2.2, A2.3... (Actividades del Componente 2)
- Cada ítem presupuestal vinculado a una actividad específica

💰 **CATEGORÍAS PRESUPUESTALES ESTÁNDAR** (usar exactamente estos nombres):
1. **Personal Técnico y Profesional**
2. **Equipamiento, Suministros y Materiales**
3. **Viajes, Transporte y Logística**
4. **Capacitación, Talleres y Eventos**
5. **Gastos Operativos y Servicios**
6. **Costos Administrativos** (máximo 10% del total)
7. **Gastos Financieros y Bancarios**
8. **Contingencias** (5-7% del presupuesto total)

📋 **DETALLES OBLIGATORIOS POR ÍTEM**:
- Código presupuestal único (formato X.Y.Z)
- Código de actividad vinculada (A1.1, A2.3, etc.)
- Descripción técnica completa y específica
- Justificación clara del ítem
- Unidad de medida precisa
- Cantidad exacta requerida
- Costo unitario en USD (con referencia al mercado guatemalteco)
- Número de meses de aplicación
- Fase del proyecto (Inicio/Implementación/Cierre)
- Tipo de costo (Local/Internacional/Mixto)
- Método de adquisición sugerido
- Responsable de la ejecución

🌍 **CONSIDERACIONES ESPECÍFICAS PARA GUATEMALA**:
- Costos locales calculados en Quetzales y convertidos a USD (tasa: 7.80 GTQ/USD)
- Salarios acordes al mercado laboral guatemalteco y estándares internacionales
- Costos de transporte considerando distancias y condiciones viales en {project_info.get('department', 'el área del proyecto')}
- Cumplimiento con regulaciones fiscales guatemaltecas (IVA, ISR, etc.)
- Consideraciones especiales para trabajo con comunidades indígenas
- Factores de ajuste por ubicación geográfica y accesibilidad

📊 **ANÁLISIS Y REPORTES REQUERIDOS**:

1. **Resumen Ejecutivo Financiero**
2. **Desglose por Categoría** (con porcentajes del total)
3. **Análisis por Actividad** (costo por actividad y su justificación)
4. **Distribución por Fase del Proyecto** (Inicio/Implementación/Cierre)
5. **Clasificación por Tipo de Costo** (Local/Internacional/Mixto)
6. **Distribución Geográfica** (si aplica por ubicaciones)
7. **Cronograma de Desembolsos** (mensual y trimestral)
8. **Análisis de Eficiencia** (costo por beneficiario, ratios clave)
9. **Evaluación de Riesgos Presupuestales**

🔍 **CUMPLIMIENTO NORMATIVO Y ESTÁNDARES**:
- Alineación con estándares del donante especificado
- Elegibilidad de todos los costos propuestos
- Mecanismos de control interno y auditoría
- Procedimientos de adquisiciones transparentes
- Sistemas de seguimiento financiero
- Reportería financiera programada

⚖️ **PRINCIPIOS DE GESTIÓN FINANCIERA DE IEPADES**:
- Transparencia absoluta en el manejo de recursos
- Eficiencia en la utilización de fondos
- Rendición de cuentas a donantes y beneficiarios
- Controles internos robustos
- Gestión de riesgos financieros
- Maximización del impacto por dólar invertido

🎯 **CRITERIOS DE CALIDAD PRESUPUESTAL**:
✓ **REALISMO**: Costos basados en investigación de mercado guatemalteco
✓ **INTEGRALIDAD**: Incluye todos los costos necesarios para el éxito del proyecto
✓ **EFICIENCIA**: Optimiza recursos para maximizar impacto
✓ **TRANSPARENCIA**: Cálculos claros y justificaciones sólidas
✓ **FLEXIBILIDAD**: Permite ajustes durante la implementación
✓ **SOSTENIBILIDAD**: Considera costos de continuidad post-proyecto
✓ **CUMPLIMIENTO**: Adhiere a todas las regulaciones aplicables

INSTRUCCIONES ESPECÍFICAS:
• Generar mínimo 40-60 líneas presupuestales detalladas
• Cada línea debe tener justificación técnica sólida
• Incluir costos diferenciados por área geográfica si es relevante
• Considerar inflación y fluctuaciones de tipo de cambio
• Incorporar mecanismos de control de calidad y supervisión
• Asegurar que el presupuesto refleje la experiencia y capacidades de IEPADES
• Demostrar conocimiento profundo del contexto guatemalteco
• Incluir innovaciones metodológicas que agreguen valor

El presupuesto debe ser técnicamente impecable, financieramente sólido y estratégicamente alineado con los objetivos del proyecto, demostrando la capacidad profesional de IEPADES para gestionar recursos de desarrollo de manera eficiente y transparente.
"""

    def _get_comprehensive_budget_schema(self) -> Dict[str, Any]:
        """Get comprehensive budget schema"""
        return {
            "currency": "USD",
            "exchange_rate": 7.80,
            "project_duration_months": "integer",

            "items": [
                {
                    "code": "string (formato X.Y.Z - ej: 1.1.1)",
                    "activity_code": "string (formato AX.Y - ej: A1.1)",
                    "activity_name": "string (nombre completo de la actividad)",
                    "category": "string (categoría presupuestal principal)",
                    "subcategory": "string (subcategoría específica)",
                    "description": "string (descripción técnica detallada)",
                    "unit": "string (unidad de medida - mes, unidad, evento, etc.)",
                    "qty": "number (cantidad requerida)",
                    "unit_cost": "number (costo unitario en USD)",
                    "months": "number (número de meses de aplicación)",
                    "phase": "string (Inicio/Implementación/Cierre)",
                    "cost_type": "string (Local/Internacional/Mixto)",
                    "justification": "string (justificación técnica detallada)",
                    "procurement_method": "string (método de adquisición)",
                    "responsible_unit": "string (unidad responsable - IEPADES/Consultor/Proveedor)",
                    "donor_eligible": "boolean (elegible según estándares del donante)",
                    "requires_approval": "boolean (requiere aprobación previa)",
                    "geographic_location": "string (ubicación específica si aplica)",
                    "risk_level": "string (Bajo/Medio/Alto)",
                    "sustainability_consideration": "string (consideración de sostenibilidad)"
                }
            ],

            "summary_by_category": {"string": "number"},
            "summary_by_activity": [
                {
                    "activity_code": "string",
                    "activity_name": "string",
                    "total_amount": "number",
                    "percentage_of_total": "number",
                    "main_categories": {"string": "number"},
                    "phase": "string",
                    "priority": "string (Alta/Media/Baja)"
                }
            ],
            "summary_by_phase": {"string": "number"},
            "summary_by_cost_type": {"string": "number"},

            "geographic_breakdown": [
                {
                    "location": "string (ubicación específica)",
                    "amount": "number",
                    "percentage": "number",
                    "main_items": ["string"],
                    "accessibility_factor": "number (factor de dificultad de acceso)"
                }
            ],

            "timeline_breakdown": {
                "monthly_distribution": {"string": "number"},
                "quarterly_milestones": {"string": {"string": "number"}},
                "critical_payment_dates": ["string"]
            },

            "financial_totals": {
                "subtotal": "number (total antes de administrativos y contingencias)",
                "administrative_cost": "number",
                "administrative_percentage": "number (máximo 10%)",
                "contingency_amount": "number",
                "contingency_percentage": "number (5-7%)",
                "total": "number (gran total del presupuesto)"
            },

            "efficiency_analysis": {
                "cost_per_beneficiary_direct": "number",
                "cost_per_beneficiary_indirect": "number",
                "budget_efficiency_ratio": "number",
                "administrative_efficiency": "number",
                "technical_vs_admin_ratio": "number"
            },

            "assumptions": ["string (supuestos presupuestales clave)"],

            "compliance_framework": [
                {
                    "regulation": "string (regulación o estándar)",
                    "requirement": "string (requerimiento específico)",
                    "compliance_status": "string (Completo/Parcial/Pendiente)",
                    "notes": "string (notas adicionales)",
                    "responsible_party": "string"
                }
            ],

            "risk_assessment": [
                {
                    "risk_category": "string (Financiero/Operativo/Técnico/Externo)",
                    "risk_description": "string",
                    "probability": "string (Baja/Media/Alta)",
                    "impact": "string (Bajo/Medio/Alto)",
                    "risk_score": "number (1-9)",
                    "mitigation_measure": "string",
                    "budget_impact": "number",
                    "contingency_allocated": "number",
                    "responsible_party": "string"
                }
            ],

            "procurement_plan": [
                {
                    "item_category": "string",
                    "procurement_method": "string",
                    "estimated_timeline": "string",
                    "approval_required": "boolean",
                    "estimated_amount": "number",
                    "vendor_requirements": "string"
                }
            ],

            "capacity_building_investment": {
                "total_amount": "number",
                "percentage_of_budget": "number",
                "beneficiary_institutions": ["string"],
                "sustainability_measures": ["string"]
            },

            "monitoring_evaluation_budget": {
                "total_me_cost": "number",
                "percentage_of_budget": "number",
                "internal_monitoring": "number",
                "external_evaluation": "number",
                "participatory_evaluation": "number"
            },

            "innovation_technology": {
                "digital_tools_budget": "number",
                "innovation_activities": "number",
                "technology_transfer": "number",
                "knowledge_management": "number"
            },

            "gender_inclusion": {
                "gender_specific_activities": "number",
                "women_participation_incentives": "number",
                "gender_sensitive_materials": "number",
                "total_gender_budget": "number"
            },

            "environmental_considerations": {
                "environmental_safeguards_cost": "number",
                "climate_adaptation_measures": "number",
                "sustainable_practices_cost": "number",
                "environmental_monitoring": "number"
            },

            "metadata": {
                "budget_version": "string",
                "preparation_date": "string",
                "prepared_by": "string",
                "reviewed_by": "string",
                "approval_status": "string",
                "currency_date": "string",
                "last_updated": "string"
            },

            "iepades_value_added": {
                "expertise_areas_budget": {"string": "number"},
                "local_capacity_building": "number",
                "community_participation_mechanisms": "number",
                "cultural_adaptation_costs": "number",
                "institutional_strengthening": "number"
            },

            "donor_specific_requirements": {
                "eligible_costs_total": "number",
                "non_eligible_costs_total": "number",
                "cost_share_required": "number",
                "reporting_costs": "number",
                "audit_costs": "number"
            },

            "performance_indicators": [
                {
                    "indicator": "string",
                    "target": "string",
                    "budget_allocation": "number",
                    "measurement_cost": "number",
                    "baseline_cost": "number"
                }
            ],

            "lessons_learned_integration": [
                "string (lecciones de proyectos anteriores de IEPADES aplicadas al presupuesto)"
            ]
        }

    def _get_error_result(self, task_type: str, error_message: str) -> Any:
        """Generate appropriate error result based on task type"""
        if task_type == "narrative":
            return f"Error generando narrativa: {error_message}\n\nNo se pudo completar la generación automática. Por favor revise la configuración y los términos de referencia."
        else:
            return {
                "error": error_message,
                "currency": "USD",
                "items": [],
                "summary_by_category": {},
                "total": 0.0,
                "assumptions": [f"Error en generación: {error_message}"],
                "compliance_notes": [],
                "processing_stats": self.processing_stats,
                "generated_at": datetime.now().isoformat(),
                "error_type": "generation_failure"
            }

    def get_processing_stats(self) -> Dict[str, Any]:
        """Get processing statistics"""
        return self.processing_stats.copy()


# Backward compatibility - maintain the original class name
class ChainedPromptGenerator(EnhancedChainedPromptGenerator):
    """Backward compatibility wrapper"""
    pass


# Utility functions for advanced token management
def optimize_chunk_distribution(chunks: List[Dict[str, Any]],
                               target_chunks: int) -> List[Dict[str, Any]]:
    """Optimize chunk distribution for better processing"""
    if len(chunks) <= target_chunks:
        return chunks

    # Combine smaller chunks while respecting token limits
    optimized_chunks = []
    current_group = []
    current_tokens = 0
    max_tokens_per_group = max(chunk.get("tokens_estimated", 0) for chunk in chunks) * 1.5

    for chunk in chunks:
        chunk_tokens = chunk.get("tokens_estimated", 0)

        if current_tokens + chunk_tokens <= max_tokens_per_group and len(current_group) < 3:
            current_group.append(chunk)
            current_tokens += chunk_tokens
        else:
            if current_group:
                optimized_chunks.append(_combine_chunks(current_group))
            current_group = [chunk]
            current_tokens = chunk_tokens

    if current_group:
        optimized_chunks.append(_combine_chunks(current_group))

    return optimized_chunks


def _combine_chunks(chunks: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Combine multiple chunks into one"""
    combined_content = "\n\n".join(chunk.get("content", "") for chunk in chunks)
    combined_section = " + ".join(chunk.get("section", "") for chunk in chunks)
    combined_tokens = sum(chunk.get("tokens_estimated", 0) for chunk in chunks)

    return {
        "content": combined_content,
        "section": combined_section,
        "tokens_estimated": combined_tokens,
        "chunk_id": TokenManager._generate_chunk_id(combined_content),
        "combined_from": len(chunks),
        "original_chunks": [chunk.get("chunk_id", "") for chunk in chunks]
    }


def estimate_processing_time(chunks: List[Dict[str, Any]],
                             provider: str) -> Dict[str, float]:
    """Estimate processing time based on chunks and provider"""

    # Base processing times (seconds per 1000 tokens)
    provider_speeds = {
        "deepseek": 2.5,  # seconds per 1000 tokens
        "sonnet": 1.8,
        "claude": 1.8,
        "anthropic": 1.8
    }

    speed = provider_speeds.get(provider.lower(), 3.0)
    total_tokens = sum(chunk.get("tokens_estimated", 0) for chunk in chunks)

    # Base processing time
    base_time = (total_tokens / 1000) * speed

    # Additional time for multi-chunk processing
    if len(chunks) > 1:
        chain_overhead = len(chunks) * 2  # 2 seconds overhead per chunk
        base_time += chain_overhead

    # Add buffer for potential retries and API delays
    buffered_time = base_time * 1.4

    return {
        "estimated_seconds": buffered_time,
        "estimated_minutes": buffered_time / 60,
        "total_tokens": total_tokens,
        "chunks_count": len(chunks),
        "provider_speed": speed
    }