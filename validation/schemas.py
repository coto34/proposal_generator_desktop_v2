from pydantic import BaseModel
from typing import Literal, List, Optional, Dict

class ProjectInput(BaseModel):
    title: str
    country: str
    language: Literal["es","en"]
    donor: str
    duration_months: int
    budget_cap: Optional[float] = None
    org_profile: str

class BudgetItem(BaseModel):
    code: str
    category: str
    description: str
    unit: str
    qty: float
    unit_cost: float
    months: Optional[int] = None
    phase: Optional[Literal["Inicio","Ejecución","Cierre"]] = None
    justification: str

class BudgetResult(BaseModel):
    currency: str
    items: List[BudgetItem]
    summary_by_category: Dict[str, float]
    total: float
    assumptions: List[str]
    compliance_notes: List[str]
