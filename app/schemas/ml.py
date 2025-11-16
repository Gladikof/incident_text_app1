"""Schemas for ML monitoring endpoints."""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel

from app.core.enums import PriorityEnum, CategoryEnum, TriageReasonEnum
from app.schemas.ticket import UserBrief


class MLPredictionLogOut(BaseModel):
    id: int
    ticket_id: int
    ticket_title: Optional[str] = None
    ticket_description: Optional[str] = None
    created_at: datetime
    model_version: Optional[str] = None
    priority_predicted: Optional[PriorityEnum] = None
    priority_confidence: Optional[float] = None
    priority_llm_predicted: Optional[PriorityEnum] = None
    priority_llm_confidence: Optional[float] = None
    priority_final: Optional[PriorityEnum] = None
    priority_feedback_previous: Optional[PriorityEnum] = None
    priority_feedback_reason: Optional[str] = None
    priority_feedback_author: Optional[UserBrief] = None
    priority_feedback_recorded_at: Optional[datetime] = None
    triage_reason: Optional[TriageReasonEnum] = None
    category_predicted: Optional[CategoryEnum] = None
    category_confidence: Optional[float] = None
    category_llm_predicted: Optional[CategoryEnum] = None
    category_llm_confidence: Optional[float] = None
    category_final: Optional[CategoryEnum] = None
    ensemble_confidence: Optional[float] = None
    ensemble_strategy: Optional[str] = None
    ensemble_reasoning: Optional[str] = None
    ensemble_category: Optional[CategoryEnum] = None
    ensemble_category_confidence: Optional[float] = None
    ensemble_category_strategy: Optional[str] = None
    ensemble_category_reasoning: Optional[str] = None
    input_text: Optional[str] = None

    class Config:
        from_attributes = True
