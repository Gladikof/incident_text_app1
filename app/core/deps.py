"""
FastAPI dependencies
"""
from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.database import get_db
from app.core.security import decode_access_token
from app.core.enums import RoleEnum
from app.models.user import User


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


def get_current_user(
    db: Session = Depends(get_db),
    token: str = Depends(oauth2_scheme)
) -> User:
    """
    Отримати поточного користувача з JWT token
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    payload = decode_access_token(token)
    if payload is None:
        raise credentials_exception

    user_id_str = payload.get("sub")
    if user_id_str is None:
        raise credentials_exception

    try:
        user_id = int(user_id_str)
    except (ValueError, TypeError):
        raise credentials_exception

    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise credentials_exception

    if not user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")

    return user


def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """Перевірити, що користувач активний"""
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user


def require_role(required_role: RoleEnum):
    """
    Dependency factory для перевірки ролі користувача
    """
    def check_role(current_user: User = Depends(get_current_active_user)):
        # ADMIN має доступ до всього
        if current_user.role == RoleEnum.ADMIN:
            return current_user

        # Інакше перевіряємо точну роль
        if current_user.role != required_role:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Not enough permissions. Required role: {required_role}"
            )
        return current_user

    return check_role


def require_admin(current_user: User = Depends(get_current_active_user)) -> User:
    """Тільки ADMIN"""
    if current_user.role != RoleEnum.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    return current_user


def require_lead_or_admin(current_user: User = Depends(get_current_active_user)) -> User:
    """LEAD або ADMIN"""
    if current_user.role not in [RoleEnum.LEAD, RoleEnum.ADMIN]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Lead or Admin access required"
        )
    return current_user


def require_agent_or_higher(current_user: User = Depends(get_current_active_user)) -> User:
    """AGENT, LEAD або ADMIN"""
    if current_user.role not in [RoleEnum.AGENT, RoleEnum.LEAD, RoleEnum.ADMIN]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Agent access or higher required"
        )
    return current_user
