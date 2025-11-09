from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field

from .models import BusinessCriticality, TicketPriority, TicketStatus, UserRole


class IncidentIn(BaseModel):
    """
    Вхідна модель: користувач задає тільки текст.
    """
    title: str = Field(..., description="Короткий заголовок інциденту")
    description: str = Field(..., description="Опис інциденту")


class ProbItem(BaseModel):
    label: str = Field(..., description="Назва класу")
    score: float = Field(..., description="Ймовірність (0..1)")


class IncidentOut(BaseModel):
    """
    Вихідна модель для класичної ML-моделі (scikit-learn).
    """
    category: str
    category_confidence: float

    priority: str
    priority_confidence: float

    explanation: str

    top_categories: List[ProbItem] = []
    top_priorities: List[ProbItem] = []


class LLMIncidentOut(BaseModel):
    """
    Вихід для LLM-маршрутизатора.
    """
    category: str
    priority: str
    urgency: str | None = None
    team: str | None = None
    assignee: str | None = None
    auto_assign: bool = False
    reasoning: str | None = None

    # Нові поля з ML-частини
    ml_priority: str | None = None
    ml_priority_confidence: float | None = None


class DepartmentBase(BaseModel):
    name: str = Field(..., max_length=128)
    business_criticality: BusinessCriticality = BusinessCriticality.medium


class DepartmentCreate(DepartmentBase):
    pass


class DepartmentRead(DepartmentBase):
    id: int

    class Config:
        orm_mode = True


class UserBase(BaseModel):
    full_name: str = Field(..., max_length=128)
    email: str = Field(..., max_length=255)
    department_id: Optional[int] = None


class UserCreate(UserBase):
    role: UserRole = UserRole.requester


class UserRead(UserBase):
    id: int
    role: UserRole
    department_name: Optional[str] = None
    asset_ids: List[int] = []

    class Config:
        orm_mode = True


class AssetBase(BaseModel):
    type: str = Field(..., max_length=64)
    model: str = Field(..., max_length=128)
    serial_number: Optional[str] = Field(None, max_length=128)
    business_criticality: BusinessCriticality = BusinessCriticality.medium


class AssetCreate(AssetBase):
    pass


class AssetRead(AssetBase):
    id: int

    class Config:
        orm_mode = True


class TicketCreate(BaseModel):
    requester_id: int
    title: str = Field(..., max_length=255)
    description: str
    affected_asset_ids: Optional[List[int]] = None


class TicketRead(BaseModel):
    id: int
    title: str
    description: str
    requester_id: int
    requester_name: Optional[str] = None
    department_id: Optional[int] = None
    department_name: Optional[str] = None
    status: TicketStatus
    priority: TicketPriority
    ml_priority: Optional[str] = None
    ml_confidence: Optional[float] = None
    created_at: datetime
    updated_at: datetime
    affected_asset_ids: List[int] = []

    class Config:
        orm_mode = True


class TicketUpdate(BaseModel):
    status: Optional[TicketStatus] = None
    priority: Optional[TicketPriority] = None


class UserRoleUpdate(BaseModel):
    role: UserRole


class UserAssetLinkRequest(BaseModel):
    is_primary: bool = False
