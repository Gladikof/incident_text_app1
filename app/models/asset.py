"""
Asset model
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship

from app.database import Base


class Asset(Base):
    """
    Модель активу (обладнання, програма тощо)
    """
    __tablename__ = "assets"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    asset_type = Column(String(100), nullable=True)  # Laptop, Server, Software, etc.
    description = Column(Text, nullable=True)

    # Відношення
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=True)
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=True)

    # Метадані
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    department = relationship("Department", back_populates="assets")
    owner = relationship("User", back_populates="owned_assets")
    tickets = relationship("Ticket", back_populates="asset")

    def __repr__(self):
        return f"<Asset {self.name} ({self.asset_type})>"
