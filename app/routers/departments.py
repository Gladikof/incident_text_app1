from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from .. import models, schemas
from ..dependencies import get_db, require_roles

router = APIRouter(prefix="/departments", tags=["departments"])


@router.get("", response_model=list[schemas.DepartmentRead])
def list_departments(db: Session = Depends(get_db)) -> list[schemas.DepartmentRead]:
    departments = db.query(models.Department).order_by(models.Department.name.asc()).all()
    return [schemas.DepartmentRead.from_orm(dep) for dep in departments]


@router.post("", response_model=schemas.DepartmentRead, status_code=status.HTTP_201_CREATED)
def create_department(
    payload: schemas.DepartmentCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_roles(models.UserRole.admin)),
) -> schemas.DepartmentRead:
    existing = db.query(models.Department).filter(models.Department.name == payload.name).first()
    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Department already exists")

    department = models.Department(
        name=payload.name,
        business_criticality=payload.business_criticality,
    )
    db.add(department)
    db.commit()
    db.refresh(department)
    return schemas.DepartmentRead.from_orm(department)
