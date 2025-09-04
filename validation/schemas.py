from pydantic import BaseModel, Field, ConfigDict
from typing import Literal, List, Optional, Dict
from enum import Enum

class ProjectPhase(str, Enum):
    INICIO = "Inicio"
    EJECUCION = "Ejecución"
    CIERRE = "Cierre"

class BudgetCategory(str, Enum):
    PERSONAL = "Personal"
    EQUIPAMIENTO = "Equipamiento y Suministros"
    VIAJES = "Viajes y Transporte"
    CAPACITACION = "Capacitación y Eventos"
    OPERATIVOS = "Gastos Operativos"
    ADMINISTRATIVOS = "Costos Administrativos"
    FINANCIEROS = "Gastos Financieros"
    CONTINGENCIAS = "Contingencias"

class CostType(str, Enum):
    LOCAL = "Local"
    INTERNACIONAL = "Internacional"
    MIXTO = "Mixto"

class ProjectInput(BaseModel):
    title: str = Field(..., description="Título del proyecto")
    country: str = Field(..., description="País donde se ejecuta")
    language: Literal["es","en"] = Field(default="es")
    donor: str = Field(..., description="Donante/Financiador")
    duration_months: int = Field(..., description="Duración en meses")
    budget_cap: Optional[float] = Field(None, description="Tope presupuestal")
    
    # Enhanced location fields
    coverage_type: Optional[str] = Field(None, description="Cobertura del proyecto")
    department: Optional[str] = Field(None, description="Departamento")
    municipality: Optional[str] = Field(None, description="Municipio")
    community: Optional[str] = Field(None, description="Comunidad/Aldea")
    geographic_coordinates: Optional[str] = Field(None, description="Coordenadas geográficas")
    
    # Target population
    target_population: Optional[str] = Field(None, description="Descripción población objetivo")
    beneficiaries_direct: Optional[str] = Field(None, description="Beneficiarios directos")
    beneficiaries_indirect: Optional[str] = Field(None, description="Beneficiarios indirectos")
    demographic_focus: Optional[str] = Field(None, description="Enfoque demográfico")
    
    # Organization
    org_profile: str = Field(..., description="Perfil de IEPADES")

class BudgetItem(BaseModel):
    code: str = Field(..., description="Código presupuestal (ej: 1.1.1)")
    activity_code: str = Field(..., description="Código de actividad vinculada")
    activity_name: str = Field(..., description="Nombre de la actividad")
    category: BudgetCategory = Field(..., description="Categoría presupuestal")
    subcategory: str = Field(..., description="Subcategoría específica")
    description: str = Field(..., description="Descripción detallada del ítem")
    
    # Cost calculation
    unit: str = Field(..., description="Unidad de medida")
    qty: float = Field(..., description="Cantidad")
    unit_cost: float = Field(..., description="Costo unitario")
    months: Optional[int] = Field(1, description="Número de meses")
    phase: Optional[ProjectPhase] = Field(None, description="Fase del proyecto")
    
    # Additional details
    cost_type: CostType = Field(default=CostType.LOCAL, description="Tipo de costo")
    justification: str = Field(..., description="Justificación técnica del ítem")
    procurement_method: Optional[str] = Field(None, description="Método de adquisición")
    responsible_unit: Optional[str] = Field(None, description="Unidad responsable")
    
    # Compliance and monitoring
    donor_eligible: bool = Field(True, description="Elegible según donante")
    requires_approval: bool = Field(False, description="Requiere aprobación previa")

class ActivityBudgetSummary(BaseModel):
    activity_code: str
    activity_name: str
    total_amount: float
    percentage_of_total: float
    main_categories: Dict[str, float]

class GeographicCostBreakdown(BaseModel):
    location: str
    amount: float
    percentage: float
    main_items: List[str]

class ComplianceNote(BaseModel):
    regulation: str
    requirement: str
    compliance_status: str
    notes: Optional[str] = None

class RiskAssessment(BaseModel):
    risk_category: str
    risk_description: str
    probability: Literal["Baja", "Media", "Alta"]
    impact: Literal["Bajo", "Medio", "Alto"]
    mitigation_measure: str
    budget_impact: Optional[float] = None

class BudgetResult(BaseModel):
    # Use ConfigDict for Pydantic V2
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "currency": "USD",
                "exchange_rate": 7.75,
                "items": [
                    {
                        "code": "1.1.1",
                        "activity_code": "A1.1",
                        "activity_name": "Diagnóstico participativo comunitario",
                        "category": "Personal",
                        "subcategory": "Coordinador de proyecto",
                        "description": "Coordinador de proyecto con experiencia en desarrollo comunitario",
                        "unit": "mes",
                        "qty": 1,
                        "unit_cost": 2500,
                        "months": 24,
                        "phase": "Ejecución",
                        "cost_type": "Local",
                        "justification": "Coordinación general del proyecto y supervisión de actividades",
                        "procurement_method": "Contratación directa",
                        "responsible_unit": "IEPADES",
                        "donor_eligible": True,
                        "requires_approval": False
                    }
                ],
                "summary_by_category": {
                    "Personal": 75000.0,
                    "Equipamiento y Suministros": 15000.0,
                    "Viajes y Transporte": 8000.0,
                    "Capacitación y Eventos": 12000.0,
                    "Gastos Operativos": 5000.0
                },
                "total": 125000.0
            }
        }
    )
    
    # Basic budget info
    currency: str = Field(default="USD", description="Moneda del presupuesto")
    exchange_rate: Optional[float] = Field(None, description="Tasa de cambio USD/GTQ")
    
    # Detailed budget items
    items: List[BudgetItem] = Field(..., description="Items presupuestales detallados")
    
    # Summary by different dimensions
    summary_by_category: Dict[str, float] = Field(..., description="Resumen por categoría")
    summary_by_activity: List[ActivityBudgetSummary] = Field(..., description="Resumen por actividad")
    summary_by_phase: Dict[str, float] = Field(..., description="Resumen por fase")
    summary_by_cost_type: Dict[str, float] = Field(..., description="Resumen por tipo de costo")
    
    # Geographic breakdown
    geographic_breakdown: List[GeographicCostBreakdown] = Field(..., description="Desglose geográfico")
    
    # Totals and percentages
    subtotal: float = Field(..., description="Subtotal antes de costos administrativos")
    administrative_cost: float = Field(..., description="Costos administrativos (máx 10%)")
    administrative_percentage: float = Field(..., description="Porcentaje administrativo")
    contingency_amount: float = Field(..., description="Monto de contingencias")
    contingency_percentage: float = Field(..., description="Porcentaje de contingencias")
    total: float = Field(..., description="Total general del presupuesto")
    
    # Budget analysis
    budget_efficiency_ratio: float = Field(..., description="Ratio de eficiencia presupuestal")
    cost_per_beneficiary: Optional[float] = Field(None, description="Costo por beneficiario directo")
    
    # Compliance and assumptions
    assumptions: List[str] = Field(..., description="Supuestos presupuestales")
    compliance_notes: List[ComplianceNote] = Field(..., description="Notas de cumplimiento normativo")
    risk_assessment: List[RiskAssessment] = Field(..., description="Evaluación de riesgos presupuestales")
    
    # Timeline and cash flow
    monthly_distribution: Dict[str, float] = Field(..., description="Distribución mensual estimada")
    quarterly_milestones: Dict[str, Dict[str, float]] = Field(..., description="Hitos trimestrales")
    
    # Quality assurance
    budget_version: str = Field(default="1.0", description="Versión del presupuesto")
    preparation_date: str = Field(..., description="Fecha de preparación")
    prepared_by: str = Field(default="IEPADES", description="Preparado por")
    reviewed_by: Optional[str] = Field(None, description="Revisado por")
    
    # Donor-specific requirements
    donor_requirements_met: bool = Field(True, description="Cumple requisitos del donante")
    eligible_costs_total: float = Field(..., description="Total de costos elegibles")
    non_eligible_costs_total: float = Field(default=0.0, description="Total de costos no elegibles")
    
    # Performance indicators
    performance_indicators: List[Dict[str, str]] = Field(
        ..., 
        description="Indicadores de desempeño relacionados con el presupuesto"
    )
    
    # Additional project-specific fields
    iepades_expertise_areas: List[str] = Field(
        default=[
            "Construcción de paz",
            "Desarrollo sostenible", 
            "Fortalecimiento comunitario",
            "Derechos humanos"
        ],
        description="Áreas de experticia de IEPADES reflejadas en el presupuesto"
    )
    
    # Environmental and social considerations
    environmental_safeguards_cost: float = Field(default=0.0, description="Costos de salvaguardas ambientales")
    social_safeguards_cost: float = Field(default=0.0, description="Costos de salvaguardas sociales")
    gender_mainstreaming_cost: float = Field(default=0.0, description="Costos de transversalización de género")