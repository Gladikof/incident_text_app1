"""
Departments Router - API endpoints для департаментів
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.core.deps import get_current_active_user, require_admin
from app.models.user import User
from app.models.department import Department
from pydantic import BaseModel


router = APIRouter(prefix="/departments", tags=["departments"])


class DepartmentOut(BaseModel):
    id: int
    name: str
    description: str | None = None
    lead_user_id: Optional[int] = None

    class Config:
        from_attributes = True


class DepartmentCreate(BaseModel):
    name: str
    description: Optional[str] = None
    lead_user_id: Optional[int] = None


class DepartmentUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    lead_user_id: Optional[int] = None


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


@router.post("", response_model=DepartmentOut)
def create_department(
    dept_data: DepartmentCreate,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """
    Створити новий департамент.

    Доступно: тільки ADMIN.
    """
    # Перевірка унікальності імені
    existing = db.query(Department).filter(Department.name == dept_data.name).first()
    if existing:
        raise HTTPException(status_code=400, detail="Department with this name already exists")

    # Перевірка LEAD якщо вказано
    if dept_data.lead_user_id is not None:
        lead_user = db.query(User).filter(User.id == dept_data.lead_user_id).first()
        if not lead_user:
            raise HTTPException(status_code=400, detail="Lead user not found")
        if lead_user.role not in ['LEAD', 'ADMIN']:
            raise HTTPException(status_code=400, detail="User must have LEAD or ADMIN role")

    new_dept = Department(
        name=dept_data.name,
        description=dept_data.description,
        lead_user_id=dept_data.lead_user_id
    )
    db.add(new_dept)
    db.commit()
    db.refresh(new_dept)
    return new_dept


@router.get("/{dept_id}", response_model=DepartmentOut)
def get_department(
    dept_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """
    Отримати інформацію про департамент.

    Доступно: всім авторизованим користувачам.
    """
    dept = db.query(Department).filter(Department.id == dept_id).first()
    if not dept:
        raise HTTPException(status_code=404, detail="Department not found")
    return dept


@router.patch("/{dept_id}", response_model=DepartmentOut)
def update_department(
    dept_id: int,
    dept_data: DepartmentUpdate,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """
    Оновити дані департаменту.

    Доступно: тільки ADMIN.
    """
    dept = db.query(Department).filter(Department.id == dept_id).first()
    if not dept:
        raise HTTPException(status_code=404, detail="Department not found")

    if dept_data.name is not None:
        # Перевірка унікальності нового імені
        existing = db.query(Department).filter(
            Department.name == dept_data.name,
            Department.id != dept_id
        ).first()
        if existing:
            raise HTTPException(status_code=400, detail="Department with this name already exists")
        dept.name = dept_data.name

    if dept_data.description is not None:
        dept.description = dept_data.description

    if dept_data.lead_user_id is not None:
        # Перевірка LEAD
        lead_user = db.query(User).filter(User.id == dept_data.lead_user_id).first()
        if not lead_user:
            raise HTTPException(status_code=400, detail="Lead user not found")
        if lead_user.role not in ['LEAD', 'ADMIN']:
            raise HTTPException(status_code=400, detail="User must have LEAD or ADMIN role")
        dept.lead_user_id = dept_data.lead_user_id

    db.commit()
    db.refresh(dept)
    return dept


@router.delete("/{dept_id}")
def delete_department(
    dept_id: int,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """
    Видалити департамент.

    Доступно: тільки ADMIN.
    """
    dept = db.query(Department).filter(Department.id == dept_id).first()
    if not dept:
        raise HTTPException(status_code=404, detail="Department not found")

    # Перевірка чи є користувачі або тікети в цьому департаменті
    users_count = db.query(User).filter(User.department_id == dept_id).count()
    if users_count > 0:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot delete department with {users_count} users. Reassign users first."
        )

    db.delete(dept)
    db.commit()

    return {"success": True, "message": "Department deleted"}
