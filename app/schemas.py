from pydantic import BaseModel, Field
from typing import List, Optional


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
    urgency: Optional[str] = None
    team: str
    assignee: Optional[str] = None
    auto_assign: bool
    reasoning: str
