"""
Ticket schemas
"""
from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field

from app.core.enums import StatusEnum, PriorityEnum, CategoryEnum, TriageReasonEnum, RoleEnum


class MLBadge(BaseModel):
    """ML Badge для UI (AUTO/REC/LOW)"""
    type: str  # "AUTO" | "REC" | "LOW"
    priority_suggested: Optional[PriorityEnum] = None
    priority_confidence: Optional[float] = None
    category_suggested: Optional[CategoryEnum] = None
    category_confidence: Optional[float] = None
    model_version: Optional[str] = None
    tooltip: Optional[str] = None


class UserBrief(BaseModel):
    """Коротка інформація про користувача для вкладення в тікет"""
    id: int
    email: str
    full_name: Optional[str] = None
    role: RoleEnum
    department_id: Optional[int] = None

    class Config:
        from_attributes = True


class DepartmentBrief(BaseModel):
    """Коротка інформація про департамент для вкладення в тікет"""
    id: int
    name: str
    description: Optional[str] = None

    class Config:
        from_attributes = True


class TicketBase(BaseModel):
    """Базові поля тікету"""
    title: str = Field(..., min_length=3, max_length=255)
    description: str = Field(..., min_length=10)
    category: Optional[CategoryEnum] = None
    asset_id: Optional[int] = None
    labels: Optional[str] = None


class TicketCreate(TicketBase):
    """Створення тікету"""
    department_id: Optional[int] = None
    priority_manual: Optional[PriorityEnum] = PriorityEnum.P3  # Дефолтний пріоритет
    skip_llm: bool = False


class TicketUpdate(BaseModel):
    """Оновлення тікету"""
    title: Optional[str] = Field(None, min_length=3, max_length=255)
    description: Optional[str] = Field(None, min_length=10)
    status: Optional[StatusEnum] = None
    category: Optional[CategoryEnum] = None
    priority_manual: Optional[PriorityEnum] = None
    labels: Optional[str] = None


class TicketStatusUpdate(BaseModel):
    """Зміна статусу"""
    status: StatusEnum


class TicketAssign(BaseModel):
    """Призначення виконавця (single)"""
    assigned_to_user_id: Optional[int] = None


class TicketAssignMultiple(BaseModel):
    """Призначення множинних виконавців"""
    assignee_ids: List[int] = Field(..., min_items=1)


class TicketTriageResolve(BaseModel):
    """????? ?? ?????????? ?????? (LEAD/ADMIN)"""
    priority_final: PriorityEnum
    category_final: CategoryEnum
    priority_change_reason: Optional[str] = None


class TicketListItem(BaseModel):
    """Тікет для списку/Board"""
    id: int
    incident_id: str
    title: str
    status: StatusEnum
    priority_manual: PriorityEnum
    category: Optional[CategoryEnum] = None

    # ML поля
    priority_ml_suggested: Optional[PriorityEnum] = None
    priority_ml_confidence: Optional[float] = None
    category_ml_suggested: Optional[CategoryEnum] = None
    category_ml_confidence: Optional[float] = None
    category_llm_suggested: Optional[CategoryEnum] = None
    category_llm_confidence: Optional[float] = None
    category_ensemble: Optional[CategoryEnum] = None
    category_ensemble_confidence: Optional[float] = None
    llm_enrichment_required: bool = False

    # Triage
    triage_required: bool
    triage_reason: Optional[TriageReasonEnum] = None

    # Relations
    assigned_to_user_id: Optional[int] = None
    department_id: Optional[int] = None
    created_by_user_id: int

    # Metadata
    labels: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    # Computed
    ml_badge: Optional[MLBadge] = None
    age: Optional[str] = None  # "3h", "2d"

    class Config:
        from_attributes = True


class TicketOut(TicketBase):
    """Повний тікет для деталей"""
    id: int
    incident_id: str
    status: StatusEnum
    priority_manual: PriorityEnum

    # ML поля
    priority_ml_suggested: Optional[PriorityEnum] = None
    priority_ml_confidence: Optional[float] = None
    priority_accepted: bool = False
    priority_ensemble: Optional[PriorityEnum] = None
    ensemble_confidence: Optional[float] = None
    ensemble_strategy: Optional[str] = None
    ensemble_reasoning: Optional[str] = None

    category_ml_suggested: Optional[CategoryEnum] = None
    category_ml_confidence: Optional[float] = None
    category_llm_suggested: Optional[CategoryEnum] = None
    category_llm_confidence: Optional[float] = None
    category_ensemble: Optional[CategoryEnum] = None
    category_ensemble_confidence: Optional[float] = None
    category_ensemble_strategy: Optional[str] = None
    category_ensemble_reasoning: Optional[str] = None
    category_accepted: bool = False

    ml_model_version: Optional[str] = None
    llm_enrichment_required: bool = False
    llm_enriched_at: Optional[datetime] = None

    # Triage
    triage_required: bool
    triage_reason: Optional[TriageReasonEnum] = None
    self_assign_locked: bool

    # Relations - IDs
    created_by_user_id: int
    assigned_to_user_id: Optional[int] = None
    department_id: Optional[int] = None
    asset_id: Optional[int] = None

    # Relations - Objects
    created_by: Optional[UserBrief] = None
    assigned_to: Optional[UserBrief] = None
    assignees: List[UserBrief] = []  # Multiple assignees
    department: Optional[DepartmentBrief] = None

    # Timestamps
    created_at: datetime
    updated_at: datetime
    resolved_at: Optional[datetime] = None
    closed_at: Optional[datetime] = None

    # Computed
    ml_badge: Optional[MLBadge] = None

    class Config:
        from_attributes = True
