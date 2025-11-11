"""
Asset schemas
"""
from typing import Optional
from datetime import datetime
from pydantic import BaseModel


class AssetBase(BaseModel):
    """Базові поля активу"""
    name: str
    asset_type: Optional[str] = None
    description: Optional[str] = None
    department_id: Optional[int] = None
    owner_id: Optional[int] = None


class AssetCreate(AssetBase):
    """Створення активу"""
    pass


class AssetUpdate(BaseModel):
    """Оновлення активу"""
    name: Optional[str] = None
    asset_type: Optional[str] = None
    description: Optional[str] = None
    department_id: Optional[int] = None
    owner_id: Optional[int] = None


class AssetOut(AssetBase):
    """Актив для відповіді"""
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
