"""
MLPredictionLog model
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Enum as SQLEnum, Text
from sqlalchemy.orm import relationship

from app.database import Base
from app.core.enums import PriorityEnum, CategoryEnum, TriageReasonEnum


class MLPredictionLog(Base):
    """
    Лог ML прогнозів для аналізу та покращення моделі
    """
    __tablename__ = "ml_prediction_logs"

    id = Column(Integer, primary_key=True, index=True)

    # Відношення до тікету
    ticket_id = Column(Integer, ForeignKey("tickets.id"), nullable=False, index=True)

    # Прогнози ML
    priority_predicted = Column(SQLEnum(PriorityEnum), nullable=True)
    priority_confidence = Column(Float, nullable=True)
    priority_llm_predicted = Column(SQLEnum(PriorityEnum), nullable=True)
    priority_llm_confidence = Column(Float, nullable=True)
    category_predicted = Column(SQLEnum(CategoryEnum), nullable=True)
    category_confidence = Column(Float, nullable=True)

    # Фінальні значення (що встановили вручну або застосували автоматично)
    priority_final = Column(SQLEnum(PriorityEnum), nullable=True)
    category_final = Column(SQLEnum(CategoryEnum), nullable=True)
    priority_feedback_previous = Column(SQLEnum(PriorityEnum), nullable=True)
    priority_feedback_reason = Column(Text, nullable=True)
    priority_feedback_author_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    priority_feedback_recorded_at = Column(DateTime, nullable=True)

    # Метадані ML
    model_version = Column(String(50), nullable=True)
    prediction_time_ms = Column(Float, nullable=True)  # Час виконання прогнозу

    # Додаткова інформація
    input_text = Column(Text, nullable=True)  # Title + Description для історії
    notes = Column(Text, nullable=True)
    triage_reason = Column(SQLEnum(TriageReasonEnum), nullable=True)

    # Ensemble Decision (комбінування ML + LLM)
    ensemble_priority = Column(SQLEnum(PriorityEnum), nullable=True)  # Фінальне рішення ensemble
    ensemble_confidence = Column(Float, nullable=True)  # Комбінована впевненість
    ensemble_strategy = Column(String(50), nullable=True)  # Яка стратегія використана
    ensemble_reasoning = Column(Text, nullable=True)  # Пояснення рішення

    # Метадані
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    # Relationships
    ticket = relationship("Ticket", back_populates="ml_logs")
    feedback_author = relationship(
        "User",
        foreign_keys=[priority_feedback_author_id],
        back_populates="ml_feedback_logs",
    )

    def __repr__(self):
        return f"<MLLog for Ticket #{self.ticket_id}>"
