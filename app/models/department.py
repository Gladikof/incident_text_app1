"""
Department model
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship

from app.database import Base


class Department(Base):
    """
    Модель департаменту/підрозділу
    """
    __tablename__ = "departments"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), unique=True, nullable=False)
    description = Column(Text, nullable=True)
    lead_user_id = Column(Integer, ForeignKey("users.id"), nullable=True)  # Начальник відділу

    # Метадані
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    users = relationship("User", foreign_keys="User.department_id", back_populates="department")
    tickets = relationship("Ticket", back_populates="department")
    assets = relationship("Asset", back_populates="department")
    lead = relationship("User", foreign_keys=[lead_user_id], post_update=True)

    def __repr__(self):
        return f"<Department {self.name}>"
