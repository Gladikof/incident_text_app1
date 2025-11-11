"""
User model
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import relationship

from app.database import Base
from app.core.enums import RoleEnum


class User(Base):
    """
    Модель користувача системи
    """
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=True)

    # Роль та права
    role = Column(SQLEnum(RoleEnum), default=RoleEnum.USER, nullable=False)
    is_lead = Column(Boolean, default=False)  # Чи є керівником департаменту
    is_active = Column(Boolean, default=True)

    # Департамент
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=True)

    # Метадані
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    department = relationship("Department", back_populates="users")
    created_tickets = relationship("Ticket", foreign_keys="Ticket.created_by_user_id", back_populates="created_by")
    assigned_tickets = relationship("Ticket", foreign_keys="Ticket.assigned_to_user_id", back_populates="assigned_to")
    owned_assets = relationship("Asset", back_populates="owner")
    comments = relationship("TicketComment", back_populates="author")

    def __repr__(self):
        return f"<User {self.email} ({self.role})>"
