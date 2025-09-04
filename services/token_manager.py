# services/token_manager.py - Enhanced version with international standards
import re
import math
import logging
from typing import List, Dict, Any, Optional, Callable
from dataclasses import dataclass
from datetime import datetime
import hashlib

# NEW IMPORTS - Add these at the top
try:
    from .enhanced_budget_system import InternationalBudgetGenerator
    ENHANCED_BUDGET_AVAILABLE = True
except ImportError:
    ENHANCED_BUDGET_AVAILABLE = False
    logging.warning("Enhanced budget system not available")

try:
    from .academic_reference_system import AcademicReferenceSystem
    ACADEMIC_REFS_AVAILABLE = True
except ImportError:
    ACADEMIC_REFS_AVAILABLE = False
    logging.warning("Academic reference system not available")

try:
    from .real_time_update_system import RealTimeDataIntegrator
    REALTIME_DATA_AVAILABLE = True
except ImportError:
    REALTIME_DATA_AVAILABLE = False
    logging.warning("Real-time data system not available")


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

    # ... (keep existing chunking methods unchanged) ...

    @staticmethod
    def _generate_chunk_id(content: str) -> str:
        """Generate unique ID for chunk"""
        return hashlib.md5(content.encode('utf-8')).hexdigest()[:8]


class EnhancedChainedPromptGenerator:
    """Enhanced chained prompt generator with international standards"""

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
        
        # Initialize enhanced systems if available
        self.academic_system = None
        self.realtime_system = None
        
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
        """Enhanced chunk processing with international standards"""

        if not chunks:
            error_msg = f"No hay chunks disponibles para procesar ({task_type})"
            self.processing_stats["errors"].append(error_msg)
            return self._get_error_result(task_type, error_msg)

        start_time = datetime.now()

        try:
            self.progress_callback(f"Procesando {len(chunks)} chunk(s) para {task_type}")

            # Initialize enhanced systems
            if ACADEMIC_REFS_AVAILABLE and not self.academic_system:
                self.academic_system = AcademicReferenceSystem(project_info, chunks[0].get('content', ''))
                
            if REALTIME_DATA_AVAILABLE and not self.realtime_system:
                self.realtime_system = RealTimeDataIntegrator(project_info)

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

    def _build_enhanced_narrative_prompt(self, content: str, project_info: Dict, 
                                        is_consolidated: bool = False) -> str:
        """Build comprehensive narrative prompt with international standards"""
        
        content_type = "información consolidada de múltiples secciones" if is_consolidated else "términos de referencia"

        # Referencias internacionales específicas por donante
        donor_standards = {
            "USAID": {
                "framework": "USAID Program Cycle",
                "approach": "Results Framework, Theory of Change, CLA (Collaborating, Learning & Adapting)",
                "indicators": "USAID Standard Indicators, custom indicators aligned with Country Development Cooperation Strategy",
                "requirements": "Gender integration, environmental compliance, sustainability planning"
            },
            "BID": {
                "framework": "Marco de Efectividad en el Desarrollo (DEF)",
                "approach": "Enfoque de Gestión por Resultados, Teoría del Cambio robusta",
                "indicators": "Indicadores SMART alineados con ODS y marcos nacionales",
                "requirements": "Salvaguardas ambientales y sociales, análisis de género, sostenibilidad fiscal"
            },
            "GIZ": {
                "framework": "Capacity WORKS, Results-Based Monitoring",
                "approach": "Enfoque por competencias, desarrollo de capacidades sostenibles",
                "indicators": "Indicadores de impacto, outcome y output con líneas base",
                "requirements": "Do No Harm, análisis de conflicto, enfoque sistémico"
            },
            "AECID": {
                "framework": "Marco de Asociación País, Enfoque Basado en Derechos Humanos",
                "approach": "Teoría del Cambio participativa, enfoque territorial",
                "indicators": "Indicadores alineados con Agenda 2030 y prioridades nacionales",
                "requirements": "Pertinencia cultural, apropiación nacional, complementariedad"
            }
        }
        
        donor = project_info.get('donor', 'Internacional')
        standards = donor_standards.get(donor, donor_standards["BID"])  # BID como default
        
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

        # Get real-time context if available
        realtime_context = ""
        if self.realtime_system:
            try:
                import asyncio
                current_data = asyncio.get_event_loop().run_until_complete(
                    self.realtime_system.fetch_current_indicators()
                )
                realtime_context = self.realtime_system.generate_updated_context_section(current_data)
            except Exception as e:
                logger.warning(f"Could not fetch real-time data: {e}")

        # Get academic references if available
        academic_context = ""
        if self.academic_system:
            try:
                topic_area = self._detect_project_topic(content, project_info)
                academic_context = self.academic_system.generate_literature_review_section(topic_area)
            except Exception as e:
                logger.warning(f"Could not generate academic references: {e}")

        return f"""
ERES UN CONSULTOR SENIOR EN DESARROLLO INTERNACIONAL con 20+ años de experiencia formulando proyectos para {donor} y otros donantes multilaterales. 

ESTÁNDARES DE REFERENCIA OBLIGATORIOS:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
• Marco institucional: {standards['framework']}
• Enfoque metodológico: {standards['approach']}
• Sistema de indicadores: {standards['indicators']}
• Requisitos específicos: {standards['requirements']}

INFORMACIÓN DETALLADA DEL PROYECTO:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
• Título: {project_info.get('title', 'Proyecto de Desarrollo')}
• País: {project_info.get('country', 'Guatemala')}
• Ubicación específica: {location_str}
• Donante/Financiador: {project_info.get('donor', 'Por definir')}
• Duración del proyecto: {project_info.get('duration_months', 'N/A')} meses
• Presupuesto referencial: {project_info.get('budget_cap', 'A determinar según propuesta')}
• Idioma de la propuesta: {project_info.get('language', 'Español')}

POBLACIÓN OBJETIVO Y BENEFICIARIOS:
{population_str}

CONTEXTO NACIONAL GUATEMALA (incluir análisis específico):
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
• Plan Nacional de Desarrollo K'atun 2032: Ejes estratégicos relevantes
• Prioridades de Política Exterior guatemalteca en cooperación
• Marco legal: Ley de ONG, Ley de Consejos de Desarrollo
• Indicadores nacionales: Encovi, INE, Segeplan
• Retos específicos: {self._get_guatemala_challenges(project_info)}

{realtime_context}

PERFIL DETALLADO DE IEPADES:
{project_info.get('org_profile', 'Ver contexto institucional arriba')}

{content_type.upper()}:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
{content}

{academic_context}

ESTRUCTURA TÉCNICA REQUERIDA (15,000-20,000 palabras):
═══════════════════════════════════════════════════════

1. **RESUMEN EJECUTIVO** (1,500 palabras)
   - Síntesis del proyecto y su relevancia
   - Valor agregado único que aporta IEPADES
   - Resultados esperados con indicadores específicos
   - Inversión requerida y retorno social proyectado
   - Sostenibilidad y escalabilidad del modelo

2. **ANÁLISIS DE CONTEXTO Y JUSTIFICACIÓN** (2,500 palabras)
   2.1 Diagnóstico situacional con fuentes primarias y secundarias
   2.2 Análisis de problemas (árbol de problemas implícito)
   2.3 Análisis de stakeholders y mapeo de actores
   2.4 Análisis de género y grupos vulnerables
   2.5 Análisis de riesgos contextuales
   2.6 Ventana de oportunidad y momento político

3. **MARCO TEÓRICO Y ENFOQUES** (2,000 palabras)
   3.1 Teoría del cambio detallada con supuestos explícitos
   3.2 Enfoque basado en derechos humanos
   3.3 Enfoque de género y empoderamiento
   3.4 Principios de Do No Harm y sensibilidad al conflicto
   3.5 Complementariedad con otros actores
   3.6 Alineación con marcos internacionales (ODS específicos)

4. **OBJETIVOS Y RESULTADOS** (2,000 palabras)
   4.1 Objetivo de desarrollo con indicadores de impacto
   4.2 Objetivo específico con indicadores de outcome
   4.3 Resultados esperados con indicadores de output
   4.4 Cadena de resultados con lógica vertical
   4.5 Indicadores SMART con líneas base y metas
   4.6 Supuestos críticos por nivel de objetivo

5. **ESTRATEGIA DE IMPLEMENTACIÓN** (3,000 palabras)
   5.1 Metodología de intervención paso a paso
   5.2 Componentes del proyecto detallados
   5.3 Actividades principales con secuencia lógica
   5.4 Cronograma maestro con hitos críticos
   5.5 Plan de gestión de riesgos operacionales
   5.6 Estrategia de comunicación y visibilidad

6. **APROPIACIÓN Y SOSTENIBILIDAD** (2,000 palabras)
   6.1 Estrategia de apropiación nacional/local
   6.2 Fortalecimiento de capacidades institucionales
   6.3 Sostenibilidad financiera post-proyecto
   6.4 Sostenibilidad técnica y operativa
   6.5 Sostenibilidad política e institucional
   6.6 Estrategia de salida gradual

7. **MONITOREO, EVALUACIÓN Y APRENDIZAJE** (1,500 palabras)
   7.1 Marco de M&E con teoría del cambio
   7.2 Plan de M&E con cronograma de mediciones
   7.3 Sistemas de información y reportería
   7.4 Evaluaciones programadas (medio término, final)
   7.5 Mecanismos de aprendizaje y adaptación
   7.6 Gestión del conocimiento y sistematización

8. **GESTIÓN DE PROYECTO** (1,500 palabras)
   8.1 Estructura de gobernanza y toma de decisiones
   8.2 Roles y responsabilidades institucionales
   8.3 Mecanismos de coordinación inter-institucional
   8.4 Gestión financiera y administrativa
   8.5 Gestión de adquisiciones y contrataciones
   8.6 Control de calidad y aseguramiento

ESTÁNDARES DE CALIDAD OBLIGATORIOS:
══════════════════════════════════════

✓ EVIDENCIA EMPÍRICA: Citar mínimo 25 fuentes confiables (estudios, estadísticas oficiales, marcos normativos)
✓ INDICADORES TÉCNICOS: Todos los indicadores deben cumplir criterios SMART con líneas base específicas
✓ ANÁLISIS CUANTITATIVO: Incluir datos numéricos en diagnóstico y proyecciones
✓ COHERENCIA METODOLÓGICA: Alineación total entre problema-solución-resultados-actividades
✓ PERTINENCIA CULTURAL: Demostrar comprensión profunda del contexto guatemalteco
✓ VIABILIDAD TÉCNICA: Cada estrategia debe tener justificación técnica sólida
✓ INNOVACIÓN: Incorporar al menos 3 enfoques innovadores basados en buenas prácticas

FUENTES REFERENCIALES ESPECÍFICAS A INTEGRAR:
════════════════════════════════════════════

• ENCOVI 2014, 2019 (condiciones de vida)
• Mapas de pobreza y desarrollo humano PNUD Guatemala
• Estadísticas vitales INE Guatemala
• Informes CEPAL sobre Guatemala
• Informes país USAID, BID, GIZ según corresponda
• Plan Nacional de Desarrollo K'atun: Guatemala 2032
• Informes de Desarrollo Humano específicos
• Estudios de género y pueblos indígenas FLACSO Guatemala
• Informes ICEFI sobre política fiscal y social

EXPERIENCIA DIFERENCIAL DE IEPADES A DESTACAR:
═════════════════════════════════════════════

• 30+ años de experiencia territorial en los 22 departamentos
• Metodologías propias de desarrollo comunitario validadas
• Red consolidada de facilitadores locales
• Alianzas estratégicas con organizaciones de base
• Experiencia en gestión de proyectos multi-donante
• Capacidades técnicas certificadas en áreas específicas
• Conocimiento profundo de dinámicas socio-políticas locales

La narrativa debe demostrar nivel de consultoría internacional senior, con rigor técnico equivalente a firmas como DAI, Chemonics, Abt Associates, pero con el valor agregado del conocimiento local profundo de IEPADES.

LONGITUD OBJETIVO: 15,000-20,000 palabras de contenido técnico sustantivo.
"""

    def _build_enhanced_budget_prompt(self, content: str, project_info: Dict,
                                     is_consolidated: bool = False) -> str:
        """Build comprehensive budget prompt with international standards"""

        content_type = "información consolidada de múltiples secciones" if is_consolidated else "términos de referencia"
        location_info = f"{project_info.get('municipality', 'N/A')}, {project_info.get('department', 'N/A')}, {project_info.get('country', 'Guatemala')}"

        # Enhanced budget prompt using International Budget Generator if available
        if ENHANCED_BUDGET_AVAILABLE:
            try:
                budget_generator = InternationalBudgetGenerator(project_info, content)
                enhanced_schema = budget_generator._get_comprehensive_budget_schema()
                return budget_generator._build_comprehensive_budget_prompt(content, project_info)
            except Exception as e:
                logger.warning(f"Enhanced budget system not available: {e}")

        # Fallback to enhanced prompt
        return f"""
{self.iepades_context}

GENERACIÓN DE PRESUPUESTO INTEGRAL Y DETALLADO

Basándote en la siguiente {content_type} y la información del proyecto, elabora un presupuesto extremadamente detallado que cumpla con los más altos estándares internacionales para proyectos de desarrollo.

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

DEVUELVE UN JSON DETALLADO con la siguiente estructura:
{{
  "currency": "USD",
  "exchange_rate": 7.75,
  "project_duration_months": {project_info.get('duration_months', 24)},
  "items": [
    {{
      "code": "string (formato X.Y.Z)",
      "activity_code": "string (formato AX.Y)",
      "category": "string",
      "description": "string",
      "unit": "string",
      "quantity": "number",
      "unit_cost": "number",
      "months": "number",
      "total_cost": "number",
      "justification": "string"
    }}
  ],
  "summary_by_category": {{"string": "number"}},
  "financial_totals": {{
    "subtotal": "number",
    "administrative_cost": "number",
    "contingency_amount": "number", 
    "total": "number"
  }},
  "assumptions": ["string"],
  "compliance_notes": ["string"]
}}

El presupuesto debe ser técnicamente impecable y demostrar capacidad profesional de IEPADES para gestionar recursos internacionales.
"""

    def _detect_project_topic(self, content: str, project_info: Dict) -> str:
        """Detect main project topic for academic references"""
        content_lower = content.lower()
        
        if any(word in content_lower for word in ["governance", "democracy", "participation", "citizen"]):
            return "governance"
        elif any(word in content_lower for word in ["economic", "livelihood", "income", "employment"]):
            return "economic_development" 
        elif any(word in content_lower for word in ["climate", "disaster", "resilience", "adaptation"]):
            return "climate_resilience"
        else:
            return "community_development"

    def _get_guatemala_challenges(self, project_info: Dict) -> str:
        """Get specific challenges based on project location and focus"""
        department = project_info.get('department', 'Guatemala')
        
        challenges_by_region = {
            'Alta Verapaz': 'Alta prevalencia de desnutrición crónica (70.3%), limitado acceso a servicios básicos',
            'Huehuetenango': 'Pobreza extrema (28.1%), migración, vulnerabilidad climática',
            'Quiché': 'Exclusión social histórica, pobreza multidimensional, conflictividad social',
            'San Marcos': 'Vulnerabilidad a desastres naturales, economía informal predominante',
            'Chiquimula': 'Corredor seco, inseguridad alimentaria, migración irregular',
        }
        
        return challenges_by_region.get(department, 'Desigualdad social, limitado acceso a servicios, vulnerabilidad económica')

    # ... (keep all existing methods unchanged) ...

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


# Backward compatibility - maintain the original class name
class ChainedPromptGenerator(EnhancedChainedPromptGenerator):
    """Backward compatibility wrapper"""
    pass