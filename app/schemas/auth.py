"""
Auth schemas
"""
from typing import Optional
from pydantic import BaseModel


class Token(BaseModel):
    """JWT Token response"""
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    """Дані з JWT токену"""
    user_id: Optional[int] = None
