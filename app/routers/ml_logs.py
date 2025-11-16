"""Endpoints for exposing ML/LLM prediction logs to the UI."""
from typing import List, Literal, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import and_
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
    ticket_from: Optional[int] = Query(None, ge=1, description="Minimum ticket id"),
    ticket_to: Optional[int] = Query(None, ge=1, description="Maximum ticket id"),
    feedback_type: Literal["all", "explicit", "implicit"] = Query(
        "all", description="Select only explicit or implicit feedback rows"
    ),
    priority_pair: Literal["all", "match", "mismatch"] = Query(
        "all", description="Compare ML priority vs LLM priority"
    ),
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
    else:
        if ticket_from:
            query = query.filter(MLPredictionLog.ticket_id >= ticket_from)
        if ticket_to:
            query = query.filter(MLPredictionLog.ticket_id <= ticket_to)

    if feedback_type == "explicit":
        query = query.filter(MLPredictionLog.priority_feedback_reason.isnot(None))
    elif feedback_type == "implicit":
        query = query.filter(
            and_(
                MLPredictionLog.priority_feedback_reason.is_(None),
                MLPredictionLog.priority_final == MLPredictionLog.priority_predicted,
            )
        )

    if priority_pair == "match":
        query = query.filter(
            MLPredictionLog.priority_predicted == MLPredictionLog.priority_llm_predicted
        )
    elif priority_pair == "mismatch":
        query = query.filter(
            MLPredictionLog.priority_predicted != MLPredictionLog.priority_llm_predicted
        )

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
                category_predicted=log.category_predicted,
                category_confidence=log.category_confidence,
                category_llm_predicted=log.category_llm_predicted,
                category_llm_confidence=log.category_llm_confidence,
                category_final=log.category_final,
                ensemble_strategy=log.ensemble_strategy,
                ensemble_confidence=log.ensemble_confidence,
                ensemble_reasoning=log.ensemble_reasoning,
                ensemble_category=log.ensemble_category,
                ensemble_category_confidence=log.ensemble_category_confidence,
                ensemble_category_strategy=log.ensemble_category_strategy,
                ensemble_category_reasoning=log.ensemble_category_reasoning,
                input_text=log.input_text,
            )
        )

    return results
