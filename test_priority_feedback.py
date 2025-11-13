"""Tests for manual priority feedback capture."""
from pathlib import Path

import pytest
from fastapi import HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

pytest.importorskip(
    "email_validator",
    reason="email-validator dependency required for schema imports",
)

from app.core.enums import PriorityEnum, RoleEnum, StatusEnum
from app.database import Base
from app.models.ticket import Ticket
from app.models.user import User
from app.models.ml_log import MLPredictionLog
from app.schemas.ticket import TicketUpdate
from app.services.ticket_service import ticket_service
from app.services.training_feedback_service import training_feedback_service


def _make_session():
    engine = create_engine("sqlite:///:memory:")
    TestingSessionLocal = sessionmaker(bind=engine)
    Base.metadata.create_all(bind=engine)
    return TestingSessionLocal()


def _create_user(session):
    user = User(email="agent@example.com", hashed_password="test", role=RoleEnum.AGENT)
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


def _create_ticket(session, user):
    ticket = Ticket(
        title="Printer issue",
        description="The printer is jammed and showing error E42.",
        status=StatusEnum.NEW,
        priority_manual=PriorityEnum.P3,
        created_by_user_id=user.id,
    )
    session.add(ticket)
    session.commit()
    session.refresh(ticket)
    return ticket


def test_update_ticket_requires_reason():
    session = _make_session()
    user = _create_user(session)
    ticket = _create_ticket(session, user)

    with pytest.raises(HTTPException):
        ticket_service.update_ticket(
            ticket_id=ticket.id,
            ticket_data=TicketUpdate(priority_manual=PriorityEnum.P1),
            actor=user,
            db=session,
        )

    session.close()


def test_update_ticket_records_feedback():
    session = _make_session()
    user = _create_user(session)
    ticket = _create_ticket(session, user)

    export_path: Path = training_feedback_service.export_path
    if export_path.exists():
        export_path.unlink()

    ticket_service.update_ticket(
        ticket_id=ticket.id,
        ticket_data=TicketUpdate(
            priority_manual=PriorityEnum.P1,
            priority_manual_reason="Ескалація через критичний вплив",
        ),
        actor=user,
        db=session,
    )

    log = session.query(MLPredictionLog).filter(MLPredictionLog.ticket_id == ticket.id).one()
    assert log.priority_final == PriorityEnum.P1
    assert log.priority_feedback_reason == "Ескалація через критичний вплив"
    assert log.priority_feedback_author_id == user.id

    assert export_path.exists()
    contents = export_path.read_text(encoding="utf-8")
    assert "Ескалація через критичний вплив" in contents

    export_path.unlink()
    session.close()
