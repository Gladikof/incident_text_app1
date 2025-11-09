from __future__ import annotations

from datetime import datetime, timezone
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload

from .. import models, schemas
from ..dependencies import get_current_user, get_db
from ..ml_client import predict_priority

router = APIRouter(prefix="/tickets", tags=["tickets"])


def _serialize_ticket(ticket: models.Ticket) -> schemas.TicketRead:
    return schemas.TicketRead(
        id=ticket.id,
        title=ticket.title,
        description=ticket.description,
        requester_id=ticket.requester_id,
        requester_name=ticket.requester.full_name if ticket.requester else None,
        department_id=ticket.department_id,
        department_name=ticket.department.name if ticket.department else None,
        status=ticket.status,
        priority=ticket.priority,
        ml_priority=ticket.ml_priority,
        ml_confidence=ticket.ml_confidence,
        created_at=ticket.created_at,
        updated_at=ticket.updated_at,
        affected_asset_ids=[link.asset_id for link in ticket.assets],
    )


def _load_ticket(db: Session, ticket_id: int) -> models.Ticket:
    ticket = (
        db.query(models.Ticket)
        .options(
            joinedload(models.Ticket.requester),
            joinedload(models.Ticket.department),
            joinedload(models.Ticket.assets),
        )
        .filter(models.Ticket.id == ticket_id)
        .first()
    )
    if not ticket:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ticket not found")
    return ticket


def _assert_view_permission(user: models.User, ticket: models.Ticket) -> None:
    if user.role == models.UserRole.admin:
        return
    if user.role == models.UserRole.agent:
        if user.department_id is None:
            return
        if ticket.department_id == user.department_id:
            return
    if ticket.requester_id == user.id:
        return
    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions to view ticket")


@router.post("", response_model=schemas.TicketRead, status_code=status.HTTP_201_CREATED)
def create_ticket(
    ticket_in: schemas.TicketCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
) -> schemas.TicketRead:
    requester = db.get(models.User, ticket_in.requester_id)
    if not requester:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Requester not found")

    if current_user.role not in {models.UserRole.admin, models.UserRole.agent} and current_user.id != requester.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Cannot create ticket for another user")

    assets: List[models.Asset] = []
    if ticket_in.affected_asset_ids:
        asset_ids = list(dict.fromkeys(ticket_in.affected_asset_ids))
        assets = (
            db.query(models.Asset)
            .filter(models.Asset.id.in_(asset_ids))
            .all()
        )
        if len(assets) != len(asset_ids):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="One or more assets not found")
    else:
        links = (
            db.query(models.UserAsset)
            .options(joinedload(models.UserAsset.asset))
            .filter(models.UserAsset.user_id == requester.id)
            .order_by(models.UserAsset.is_primary.desc())
            .all()
        )
        primary_assets = [link.asset for link in links if link.is_primary]
        assets = primary_assets or [link.asset for link in links]

    department = requester.department
    department_name = department.name if department else None
    department_criticality = (
        getattr(department.business_criticality, "value", department.business_criticality)
        if department
        else None
    )
    asset_criticalities = [
        getattr(asset.business_criticality, "value", asset.business_criticality)
        for asset in assets
    ]

    priority_label, confidence = predict_priority(
        text=f"{ticket_in.title}\n{ticket_in.description}".strip(),
        department_name=department_name,
        department_criticality=department_criticality,
        asset_criticalities=asset_criticalities,
    )

    try:
        priority_enum = models.TicketPriority(priority_label)
    except ValueError:
        priority_enum = models.TicketPriority.P3

    ticket = models.Ticket(
        title=ticket_in.title,
        description=ticket_in.description,
        requester_id=requester.id,
        department_id=requester.department_id,
        priority=priority_enum,
        ml_priority=priority_enum.value,
        ml_confidence=confidence,
    )
    db.add(ticket)
    db.flush()

    for asset in assets:
        db.add(models.TicketAsset(ticket_id=ticket.id, asset_id=asset.id))

    db.commit()
    db.refresh(ticket)

    return _serialize_ticket(ticket)


@router.get("", response_model=List[schemas.TicketRead])
def list_tickets(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
) -> List[schemas.TicketRead]:
    query = (
        db.query(models.Ticket)
        .options(
            joinedload(models.Ticket.requester),
            joinedload(models.Ticket.department),
            joinedload(models.Ticket.assets),
        )
        .order_by(models.Ticket.created_at.desc())
    )

    if current_user.role == models.UserRole.admin:
        tickets = query.all()
    elif current_user.role == models.UserRole.agent:
        if current_user.department_id is None:
            tickets = query.all()
        else:
            tickets = query.filter(models.Ticket.department_id == current_user.department_id).all()
    else:
        tickets = query.filter(models.Ticket.requester_id == current_user.id).all()

    return [_serialize_ticket(ticket) for ticket in tickets]


@router.get("/{ticket_id}", response_model=schemas.TicketRead)
def get_ticket(
    ticket_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
) -> schemas.TicketRead:
    ticket = _load_ticket(db, ticket_id)
    _assert_view_permission(current_user, ticket)
    return _serialize_ticket(ticket)


@router.patch("/{ticket_id}", response_model=schemas.TicketRead)
def update_ticket(
    ticket_id: int,
    payload: schemas.TicketUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
) -> schemas.TicketRead:
    ticket = _load_ticket(db, ticket_id)
    if current_user.role not in {models.UserRole.admin, models.UserRole.agent}:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")

    if current_user.role == models.UserRole.agent and current_user.department_id and ticket.department_id != current_user.department_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Cannot update ticket outside your department")

    updated = False
    if payload.status is not None:
        ticket.status = payload.status
        updated = True
    if payload.priority is not None:
        ticket.priority = payload.priority
        updated = True

    if updated:
        ticket.updated_at = datetime.now(timezone.utc)
        db.add(ticket)
        db.commit()
        db.refresh(ticket)

    return _serialize_ticket(ticket)
