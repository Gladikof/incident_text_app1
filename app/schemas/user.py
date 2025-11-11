"""
User schemas
"""
from typing import Optional
from datetime import datetime
from pydantic import BaseModel, EmailStr, Field

from app.core.enums import RoleEnum


class UserBase(BaseModel):
    """Базові поля користувача"""
    email: EmailStr
    full_name: Optional[str] = None
    role: RoleEnum = RoleEnum.USER
    is_lead: bool = False
    department_id: Optional[int] = None


class UserCreate(UserBase):
    """Створення користувача"""
    password: str = Field(..., min_length=6)


class UserUpdate(BaseModel):
    """Оновлення користувача"""
    full_name: Optional[str] = None
    role: Optional[RoleEnum] = None
    is_lead: Optional[bool] = None
    department_id: Optional[int] = None
    is_active: Optional[bool] = None


class UserOut(UserBase):
    """Користувач для відповіді"""
    id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class UserLogin(BaseModel):
    """Логін"""
    email: EmailStr
    password: str
