"""
Users Router - API endpoints для управління користувачами (admin)
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr

from app.database import get_db
from app.core.deps import require_admin
from app.core.enums import RoleEnum
from app.models.user import User
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

router = APIRouter(prefix="/admin/users", tags=["admin", "users"])


class UserOut(BaseModel):
    id: int
    email: str
    full_name: Optional[str]
    role: RoleEnum
    is_lead: bool
    is_active: bool
    department_id: Optional[int]
    specialty: Optional[str]

    class Config:
        from_attributes = True


class UserCreate(BaseModel):
    email: EmailStr
    password: str
    full_name: Optional[str] = None
    role: RoleEnum = RoleEnum.USER
    is_lead: bool = False
    is_active: bool = True
    department_id: Optional[int] = None
    specialty: Optional[str] = None


class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    role: Optional[RoleEnum] = None
    is_lead: Optional[bool] = None
    is_active: Optional[bool] = None
    department_id: Optional[int] = None
    specialty: Optional[str] = None
    password: Optional[str] = None  # Якщо передано - оновити пароль


@router.get("", response_model=List[UserOut])
def list_users(
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """
    Отримати список всіх користувачів.

    Доступно: тільки ADMIN.
    """
    users = db.query(User).all()
    return users


@router.post("", response_model=UserOut)
def create_user(
    user_data: UserCreate,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """
    Створити нового користувача.

    Доступно: тільки ADMIN.
    """
    # Перевірка унікальності email
    existing = db.query(User).filter(User.email == user_data.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="User with this email already exists")

    # Перевірка департаменту якщо вказано
    if user_data.department_id is not None:
        from app.models.department import Department
        dept = db.query(Department).filter(Department.id == user_data.department_id).first()
        if not dept:
            raise HTTPException(status_code=400, detail="Department not found")

    # Хешування паролю
    hashed_password = pwd_context.hash(user_data.password)

    # Створення користувача
    new_user = User(
        email=user_data.email,
        hashed_password=hashed_password,
        full_name=user_data.full_name,
        role=user_data.role,
        is_lead=user_data.is_lead,
        is_active=user_data.is_active,
        department_id=user_data.department_id,
        specialty=user_data.specialty
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user


@router.get("/{user_id}", response_model=UserOut)
def get_user(
    user_id: int,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """
    Отримати інформацію про конкретного користувача.

    Доступно: тільки ADMIN.
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.patch("/{user_id}", response_model=UserOut)
def update_user(
    user_id: int,
    user_data: UserUpdate,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """
    Оновити дані користувача (email, пароль, роль, спеціалізація, тощо).

    Доступно: тільки ADMIN.
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Оновлюємо поля
    if user_data.email is not None:
        # Перевіряємо унікальність email
        existing = db.query(User).filter(
            User.email == user_data.email,
            User.id != user_id
        ).first()
        if existing:
            raise HTTPException(status_code=400, detail="Email already exists")
        user.email = user_data.email

    if user_data.full_name is not None:
        user.full_name = user_data.full_name

    if user_data.role is not None:
        user.role = user_data.role

    if user_data.is_lead is not None:
        user.is_lead = user_data.is_lead

    if user_data.is_active is not None:
        user.is_active = user_data.is_active

    if user_data.department_id is not None:
        user.department_id = user_data.department_id

    if user_data.specialty is not None:
        user.specialty = user_data.specialty

    if user_data.password is not None:
        user.hashed_password = pwd_context.hash(user_data.password)

    db.commit()
    db.refresh(user)
    return user


@router.delete("/{user_id}")
def delete_user(
    user_id: int,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """
    Видалити користувача (або деактивувати).

    Доступно: тільки ADMIN.
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Не дозволяємо видалити себе
    if user.id == current_user.id:
        raise HTTPException(status_code=400, detail="Cannot delete yourself")

    # Замість видалення - деактивуємо
    user.is_active = False
    db.commit()

    return {"success": True, "message": "User deactivated"}
