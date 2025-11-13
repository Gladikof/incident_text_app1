"""Endpoints for exposing ML/LLM prediction logs to the UI."""
from typing import List, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session, joinedload

from app.database import get_db
from app.core.deps import require_lead_or_admin
from app.models.ml_log import MLPredictionLog
from app.models.user import User
from app.schemas.ml import MLPredictionLogOut

router = APIRouter(prefix="/ml/logs", tags=["ml"])


@router.get("", response_model=List[MLPredictionLogOut])
def list_ml_logs(
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    ticket_id: Optional[int] = Query(None, description="Filter by ticket id"),
    current_user: User = Depends(require_lead_or_admin),
    db: Session = Depends(get_db),
) -> List[MLPredictionLogOut]:
    query = (
        db.query(MLPredictionLog)
        .options(
            joinedload(MLPredictionLog.ticket),
            joinedload(MLPredictionLog.feedback_author),
        )
        .order_by(MLPredictionLog.created_at.desc())
    )

    if ticket_id:
        query = query.filter(MLPredictionLog.ticket_id == ticket_id)

    logs = query.offset(offset).limit(limit).all()

    results: List[MLPredictionLogOut] = []
    for log in logs:
        results.append(
            MLPredictionLogOut(
                id=log.id,
                ticket_id=log.ticket_id,
                ticket_title=log.ticket.title if log.ticket else None,
                ticket_description=log.ticket.description if log.ticket else None,
                created_at=log.created_at,
                model_version=log.model_version,
                priority_predicted=log.priority_predicted,
                priority_confidence=log.priority_confidence,
                priority_llm_predicted=log.priority_llm_predicted,
                priority_llm_confidence=log.priority_llm_confidence,
                priority_final=log.priority_final,
                priority_feedback_previous=log.priority_feedback_previous,
                priority_feedback_reason=log.priority_feedback_reason,
                priority_feedback_author=log.feedback_author,
                priority_feedback_recorded_at=log.priority_feedback_recorded_at,
                triage_reason=log.triage_reason,
            )
        )

    return results
