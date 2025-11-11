"""
Comment schemas
"""
from datetime import datetime
from pydantic import BaseModel, Field


class CommentBase(BaseModel):
    """Базові поля коментаря"""
    content: str = Field(..., min_length=1)


class CommentCreate(CommentBase):
    """Створення коментаря"""
    pass


class CommentOut(CommentBase):
    """Коментар для відповіді"""
    id: int
    ticket_id: int
    author_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
