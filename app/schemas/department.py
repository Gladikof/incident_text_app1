"""
Department schemas
"""
from typing import Optional
from datetime import datetime
from pydantic import BaseModel


class DepartmentBase(BaseModel):
    """Базові поля департаменту"""
    name: str
    description: Optional[str] = None


class DepartmentCreate(DepartmentBase):
    """Створення департаменту"""
    pass


class DepartmentUpdate(BaseModel):
    """Оновлення департаменту"""
    name: Optional[str] = None
    description: Optional[str] = None


class DepartmentOut(DepartmentBase):
    """Департамент для відповіді"""
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
