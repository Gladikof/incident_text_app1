from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from .. import models, schemas
from ..dependencies import get_db, require_roles

router = APIRouter(prefix="/assets", tags=["assets"])


@router.get("", response_model=list[schemas.AssetRead])
def list_assets(
    db: Session = Depends(get_db),
    user_id: int | None = Query(default=None, description="Filter assets assigned to a user"),
) -> list[schemas.AssetRead]:
    query = db.query(models.Asset)
    if user_id is not None:
        query = query.join(models.UserAsset).filter(models.UserAsset.user_id == user_id)
    assets = query.order_by(models.Asset.model.asc()).all()
    return [schemas.AssetRead.from_orm(asset) for asset in assets]


@router.post("", response_model=schemas.AssetRead, status_code=status.HTTP_201_CREATED)
def create_asset(
    payload: schemas.AssetCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_roles(models.UserRole.admin)),
) -> schemas.AssetRead:
    if payload.serial_number:
        existing = (
            db.query(models.Asset)
            .filter(models.Asset.serial_number == payload.serial_number)
            .first()
        )
        if existing:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Serial number already exists")

    asset = models.Asset(
        type=payload.type,
        model=payload.model,
        serial_number=payload.serial_number,
        business_criticality=payload.business_criticality,
    )
    db.add(asset)
    db.commit()
    db.refresh(asset)
    return schemas.AssetRead.from_orm(asset)
