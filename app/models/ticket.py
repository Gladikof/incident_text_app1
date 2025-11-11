"""
Ticket model з ML полями
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, Boolean, Float, DateTime, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import relationship

from app.database import Base
from app.core.enums import StatusEnum, PriorityEnum, CategoryEnum, TriageReasonEnum


class Ticket(Base):
    """
    Модель тікету (інциденту) з повною підтримкою ML та тріажу
    """
    __tablename__ = "tickets"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)

    # === Основні поля ===
    status = Column(SQLEnum(StatusEnum), default=StatusEnum.NEW, nullable=False, index=True)
    priority_manual = Column(SQLEnum(PriorityEnum), default=PriorityEnum.P3, nullable=False)
    category = Column(SQLEnum(CategoryEnum), nullable=True)

    # === ML поля - Priority ===
    priority_ml_suggested = Column(SQLEnum(PriorityEnum), nullable=True)
    priority_ml_confidence = Column(Float, nullable=True)  # 0..1
    priority_accepted = Column(Boolean, default=False)

    # === ML поля - Category ===
    category_ml_suggested = Column(SQLEnum(CategoryEnum), nullable=True)
    category_ml_confidence = Column(Float, nullable=True)  # 0..1
    category_accepted = Column(Boolean, default=False)

    # === ML метадані ===
    ml_model_version = Column(String(50), nullable=True)

    # === Triage поля ===
    triage_required = Column(Boolean, default=False, index=True)
    triage_reason = Column(SQLEnum(TriageReasonEnum), nullable=True)
    self_assign_locked = Column(Boolean, default=False)

    # === Відношення ===
    created_by_user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    assigned_to_user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=True, index=True)
    asset_id = Column(Integer, ForeignKey("assets.id"), nullable=True)

    # === Додаткові поля ===
    labels = Column(String(500), nullable=True)  # JSON array або comma-separated

    # === Метадані ===
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    resolved_at = Column(DateTime, nullable=True)
    closed_at = Column(DateTime, nullable=True)

    # === Relationships ===
    created_by = relationship("User", foreign_keys=[created_by_user_id], back_populates="created_tickets")
    assigned_to = relationship("User", foreign_keys=[assigned_to_user_id], back_populates="assigned_tickets")
    department = relationship("Department", back_populates="tickets")
    asset = relationship("Asset", back_populates="tickets")
    comments = relationship("TicketComment", back_populates="ticket", cascade="all, delete-orphan")
    ml_logs = relationship("MLPredictionLog", back_populates="ticket", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Ticket #{self.id}: {self.title[:50]} ({self.status})>"

    @property
    def incident_id(self):
        """Форматований ID тікету (INC-0001)"""
        return f"INC-{self.id:04d}"
