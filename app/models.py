from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import List, Optional

from sqlalchemy import Boolean, DateTime, Enum as SQLEnum, Float, ForeignKey, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base


class BusinessCriticality(str, Enum):
    high = "high"
    medium = "medium"
    low = "low"


class UserRole(str, Enum):
    admin = "admin"
    agent = "agent"
    requester = "requester"


class TicketStatus(str, Enum):
    new = "new"
    in_progress = "in_progress"
    resolved = "resolved"
    closed = "closed"


class TicketPriority(str, Enum):
    P1 = "P1"
    P2 = "P2"
    P3 = "P3"
    P4 = "P4"
    P5 = "P5"


class Department(Base):
    __tablename__ = "departments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(128), unique=True, index=True, nullable=False)
    business_criticality: Mapped[str] = mapped_column(
        SQLEnum(BusinessCriticality), nullable=False, default=BusinessCriticality.medium
    )

    users: Mapped[List["User"]] = relationship("User", back_populates="department", cascade="all, delete")
    tickets: Mapped[List["Ticket"]] = relationship("Ticket", back_populates="department")


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    full_name: Mapped[str] = mapped_column(String(128), nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    role: Mapped[str] = mapped_column(SQLEnum(UserRole), nullable=False, default=UserRole.requester)
    department_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("departments.id"), nullable=True)

    department: Mapped[Optional[Department]] = relationship("Department", back_populates="users")
    assets: Mapped[List["UserAsset"]] = relationship(
        "UserAsset", back_populates="user", cascade="all, delete-orphan"
    )
    tickets: Mapped[List["Ticket"]] = relationship("Ticket", back_populates="requester")


class Asset(Base):
    __tablename__ = "assets"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    type: Mapped[str] = mapped_column(String(64), nullable=False)
    model: Mapped[str] = mapped_column(String(128), nullable=False)
    serial_number: Mapped[Optional[str]] = mapped_column(String(128), unique=True, nullable=True)
    business_criticality: Mapped[str] = mapped_column(
        SQLEnum(BusinessCriticality), nullable=False, default=BusinessCriticality.medium
    )

    user_links: Mapped[List["UserAsset"]] = relationship(
        "UserAsset", back_populates="asset", cascade="all, delete-orphan"
    )
    ticket_links: Mapped[List["TicketAsset"]] = relationship(
        "TicketAsset", back_populates="asset", cascade="all, delete-orphan"
    )


class UserAsset(Base):
    __tablename__ = "user_assets"
    __table_args__ = (UniqueConstraint("user_id", "asset_id", name="uq_user_asset"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    asset_id: Mapped[int] = mapped_column(Integer, ForeignKey("assets.id"), nullable=False)
    is_primary: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    user: Mapped["User"] = relationship("User", back_populates="assets")
    asset: Mapped["Asset"] = relationship("Asset", back_populates="user_links")


class Ticket(Base):
    __tablename__ = "tickets"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    requester_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    department_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("departments.id"), nullable=True)
    status: Mapped[str] = mapped_column(
        SQLEnum(TicketStatus), nullable=False, default=TicketStatus.new
    )
    priority: Mapped[str] = mapped_column(
        SQLEnum(TicketPriority), nullable=False, default=TicketPriority.P3
    )
    ml_priority: Mapped[Optional[str]] = mapped_column(String(16), nullable=True)
    ml_confidence: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )

    requester: Mapped["User"] = relationship("User", back_populates="tickets")
    department: Mapped[Optional[Department]] = relationship("Department", back_populates="tickets")
    assets: Mapped[List["TicketAsset"]] = relationship(
        "TicketAsset", back_populates="ticket", cascade="all, delete-orphan"
    )


class TicketAsset(Base):
    __tablename__ = "ticket_assets"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    ticket_id: Mapped[int] = mapped_column(Integer, ForeignKey("tickets.id"), nullable=False)
    asset_id: Mapped[int] = mapped_column(Integer, ForeignKey("assets.id"), nullable=False)

    ticket: Mapped["Ticket"] = relationship("Ticket", back_populates="assets")
    asset: Mapped["Asset"] = relationship("Asset", back_populates="ticket_links")
