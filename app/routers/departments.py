"""
Departments Router - API endpoints для департаментів
"""
from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.core.deps import get_current_active_user
from app.models.user import User
from app.models.department import Department
from pydantic import BaseModel


router = APIRouter(prefix="/departments", tags=["departments"])


class DepartmentOut(BaseModel):
    id: int
    name: str
    description: str | None = None

    class Config:
        from_attributes = True


@router.get("", response_model=List[DepartmentOut])
def list_departments(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """
    Список всіх департаментів.

    Доступно: всім авторизованим користувачам.
    """
    departments = db.query(Department).all()
    return departments
