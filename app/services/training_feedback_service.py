"""Service helpers for exporting ML/LLM feedback datasets."""
from __future__ import annotations

import csv
from enum import Enum
from pathlib import Path
from typing import Iterable, Optional

from sqlalchemy.orm import Session, joinedload

from app.config import settings
from app.models.ml_log import MLPredictionLog


class TrainingFeedbackService:
    """Aggregate feedback for retraining pipelines."""

    def __init__(self, export_path: Optional[Path] = None) -> None:
        self._export_path = export_path or (settings.TRAINING_DATA_DIR / "priority_feedback.csv")
        self._export_path.parent.mkdir(parents=True, exist_ok=True)

    @property
    def export_path(self) -> Path:
        return self._export_path

    def export_priority_feedback_dataset(self, db: Session) -> Path:
        """Materialise all priority feedback logs into a CSV file.

        The dataset consolidates ML and LLM predictions alongside manual
        corrections so that offline training scripts can bootstrap from a
        single artefact.
        """

        logs: Iterable[MLPredictionLog] = (
            db.query(MLPredictionLog)
            .options(
                joinedload(MLPredictionLog.ticket),
                joinedload(MLPredictionLog.feedback_author),
            )
            .filter(MLPredictionLog.priority_final.isnot(None))
            .order_by(MLPredictionLog.created_at.desc())
            .all()
        )

        with self.export_path.open("w", encoding="utf-8", newline="") as fp:
            writer = csv.DictWriter(
                fp,
                fieldnames=[
                    "ticket_id",
                    "created_at",
                    "updated_at",
                    "full_text",
                    "priority_ml",
                    "priority_ml_confidence",
                    "priority_llm",
                    "priority_llm_confidence",
                    "priority_final",
                    "priority_feedback_previous",
                    "priority_feedback_reason",
                    "priority_feedback_author",
                    "priority_feedback_recorded_at",
                    "triage_reason",
                ],
            )
            writer.writeheader()

            for log in logs:
                ticket = log.ticket
                full_text = None
                created_at = None
                updated_at = None
                if ticket is not None:
                    title = ticket.title or ""
                    description = ticket.description or ""
                    full_text = f"{title}\n{description}".strip()
                    created_at = ticket.created_at.isoformat() if ticket.created_at else None
                    updated_at = ticket.updated_at.isoformat() if ticket.updated_at else None

                writer.writerow(
                    {
                        "ticket_id": log.ticket_id,
                        "created_at": created_at,
                        "updated_at": updated_at,
                        "full_text": full_text,
                        "priority_ml": _enum_to_str(log.priority_predicted),
                        "priority_ml_confidence": log.priority_confidence,
                        "priority_llm": _enum_to_str(log.priority_llm_predicted),
                        "priority_llm_confidence": log.priority_llm_confidence,
                        "priority_final": _enum_to_str(log.priority_final),
                        "priority_feedback_previous": _enum_to_str(log.priority_feedback_previous),
                        "priority_feedback_reason": log.priority_feedback_reason,
                        "priority_feedback_author": (log.feedback_author.email if log.feedback_author else None),
                        "priority_feedback_recorded_at": (
                            log.priority_feedback_recorded_at.isoformat()
                            if log.priority_feedback_recorded_at
                            else None
                        ),
                        "triage_reason": _enum_to_str(log.triage_reason),
                    }
                )

        return self.export_path


def _enum_to_str(value: Optional[Enum]) -> Optional[str]:
    if value is None:
        return None
    return value.value if hasattr(value, "value") else str(value)


training_feedback_service = TrainingFeedbackService()
