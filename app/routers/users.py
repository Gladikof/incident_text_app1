from __future__ import annotations

from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlalchemy.orm import Session, joinedload

from .. import models, schemas
from ..dependencies import get_current_user, get_db, require_roles

router = APIRouter(prefix="/users", tags=["users"])


def _serialize_user(user: models.User) -> schemas.UserRead:
    return schemas.UserRead(
        id=user.id,
        full_name=user.full_name,
        email=user.email,
        role=user.role,
        department_id=user.department_id,
        department_name=user.department.name if user.department else None,
        asset_ids=[link.asset_id for link in user.assets],
    )


@router.get("", response_model=list[schemas.UserRead])
def list_users(db: Session = Depends(get_db)) -> list[schemas.UserRead]:
    users = (
        db.query(models.User)
        .options(joinedload(models.User.department), joinedload(models.User.assets))
        .order_by(models.User.full_name.asc())
        .all()
    )
    return [_serialize_user(user) for user in users]


@router.post("", response_model=schemas.UserRead, status_code=status.HTTP_201_CREATED)
def create_user(
    payload: schemas.UserCreate,
    db: Session = Depends(get_db),
    x_user_id: int | None = Header(default=None, alias="X-User-Id"),
) -> schemas.UserRead:
    current_user: models.User | None = db.get(models.User, x_user_id) if x_user_id else None
    if x_user_id and current_user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid X-User-Id header")
    if current_user and current_user.role != models.UserRole.admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only admins can create users")

    if not current_user and payload.role != models.UserRole.requester:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Self-registration allowed only as requester")

    existing = db.query(models.User).filter(models.User.email == payload.email).first()
    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")

    user = models.User(
        full_name=payload.full_name,
        email=payload.email,
        role=payload.role,
        department_id=payload.department_id,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return _serialize_user(user)


@router.get("/{user_id}", response_model=schemas.UserRead)
def get_user(user_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)) -> schemas.UserRead:
    if current_user.role != models.UserRole.admin and current_user.id != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Cannot view other users")

    user = (
        db.query(models.User)
        .options(joinedload(models.User.department), joinedload(models.User.assets))
        .filter(models.User.id == user_id)
        .first()
    )
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return _serialize_user(user)


@router.patch("/{user_id}/role", response_model=schemas.UserRead)
def update_user_role(
    user_id: int,
    payload: schemas.UserRoleUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_roles(models.UserRole.admin)),
) -> schemas.UserRead:
    user = (
        db.query(models.User)
        .options(joinedload(models.User.department), joinedload(models.User.assets))
        .filter(models.User.id == user_id)
        .first()
    )
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    user.role = payload.role
    db.add(user)
    db.commit()
    db.refresh(user)
    return _serialize_user(user)


@router.post("/{user_id}/assets/{asset_id}", response_model=schemas.UserRead)
def link_asset_to_user(
    user_id: int,
    asset_id: int,
    payload: schemas.UserAssetLinkRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_roles(models.UserRole.admin)),
) -> schemas.UserRead:
    user = (
        db.query(models.User)
        .options(joinedload(models.User.assets))
        .filter(models.User.id == user_id)
        .first()
    )
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    asset = db.get(models.Asset, asset_id)
    if not asset:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Asset not found")

    link = (
        db.query(models.UserAsset)
        .filter(models.UserAsset.user_id == user_id, models.UserAsset.asset_id == asset_id)
        .first()
    )
    if not link:
        link = models.UserAsset(user_id=user_id, asset_id=asset_id)
        db.add(link)

    link.is_primary = payload.is_primary

    if payload.is_primary:
        (
            db.query(models.UserAsset)
            .filter(models.UserAsset.user_id == user_id, models.UserAsset.asset_id != asset_id)
            .update({models.UserAsset.is_primary: False}, synchronize_session=False)
        )

    db.commit()
    db.refresh(user)
    db.refresh(link)
    user = (
        db.query(models.User)
        .options(joinedload(models.User.department), joinedload(models.User.assets))
        .filter(models.User.id == user_id)
        .first()
    )
    return _serialize_user(user)
