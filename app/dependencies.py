from __future__ import annotations

from typing import Callable, Iterable

from fastapi import Depends, Header, HTTPException, status
from sqlalchemy.orm import Session

from .database import SessionLocal
from .models import User, UserRole


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_current_user(
    db: Session = Depends(get_db), user_id: int | None = Header(default=None, alias="X-User-Id")
) -> User:
    if user_id is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="X-User-Id header is required")

    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    return user


def require_roles(*roles: Iterable[UserRole | str]) -> Callable[[User], User]:
    allowed = {role.value if isinstance(role, UserRole) else str(role) for role in roles}

    def _dependency(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in allowed:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")
        return current_user

    return _dependency
