"""
Pydantic schemas for API
"""
from app.schemas.user import UserOut, UserCreate, UserUpdate, UserLogin
from app.schemas.auth import Token, TokenData
from app.schemas.department import DepartmentOut, DepartmentCreate, DepartmentUpdate
from app.schemas.asset import AssetOut, AssetCreate, AssetUpdate
from app.schemas.ticket import (
    TicketOut,
    TicketCreate,
    TicketUpdate,
    TicketStatusUpdate,
    TicketAssign,
    TicketTriageResolve,
    TicketListItem,
    MLBadge,
)
from app.schemas.comment import CommentOut, CommentCreate
from app.schemas.settings import SystemSettingsOut, SystemSettingsUpdate
from app.schemas.ml import MLPredictionLogOut

__all__ = [
    "UserOut",
    "UserCreate",
    "UserUpdate",
    "UserLogin",
    "Token",
    "TokenData",
    "DepartmentOut",
    "DepartmentCreate",
    "DepartmentUpdate",
    "AssetOut",
    "AssetCreate",
    "AssetUpdate",
    "TicketOut",
    "TicketCreate",
    "TicketUpdate",
    "TicketStatusUpdate",
    "TicketAssign",
    "TicketTriageResolve",
    "TicketListItem",
    "MLBadge",
    "MLPredictionLogOut",
    "CommentOut",
    "CommentCreate",
    "SystemSettingsOut",
    "SystemSettingsUpdate",
]
