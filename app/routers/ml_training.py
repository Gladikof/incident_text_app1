"""
ML Training API - endpoints для управління навчанням ML моделей.
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.models.ml_model_metadata import MLModelMetadata, MLTrainingJob
from app.core.deps import require_admin
from app.services.active_learning_service import active_learning_service
from app.services.ml_scheduler import ml_scheduler
from pydantic import BaseModel
from datetime import datetime


# === Schemas ===


class MLModelMetadataOut(BaseModel):
    id: int
    version: str
    created_at: datetime
    accuracy: Optional[float]
    precision_p1: Optional[float]
    precision_p2: Optional[float]
    precision_p3: Optional[float]
    recall_p1: Optional[float]
    recall_p2: Optional[float]
    recall_p3: Optional[float]
    f1_score: Optional[float]
    training_samples_count: Optional[int]
    is_active: bool
    notes: Optional[str]

    class Config:
        from_attributes = True


class MLTrainingJobOut(BaseModel):
    id: int
    started_at: datetime
    completed_at: Optional[datetime]
    status: str
    model_version: Optional[str]
    new_feedback_count: Optional[int]
    total_training_samples: Optional[int]
    error_message: Optional[str]
    training_type: str

    class Config:
        from_attributes = True


class RetrainStatusOut(BaseModel):
    should_retrain: bool
    new_feedback_count: int
    reason: str
    min_feedback_threshold: int


class TriggerRetrainOut(BaseModel):
    success: bool
    job_id: Optional[int]
    message: str


class ActivateModelOut(BaseModel):
    success: bool
    message: str


# === Router ===

router = APIRouter(
    prefix="/ml/training",
    tags=["ML Training"],
)


@router.get("/status", response_model=RetrainStatusOut)
def get_retrain_status(
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """
    Перевіряє чи потрібно перенавчувати модель.
    Доступ: тільки ADMIN.
    """
    should_train, new_count, reason = active_learning_service.should_retrain(db)

    return RetrainStatusOut(
        should_retrain=should_train,
        new_feedback_count=new_count,
        reason=reason,
        min_feedback_threshold=active_learning_service.MIN_NEW_FEEDBACK_FOR_RETRAIN,
    )


@router.post("/trigger", response_model=TriggerRetrainOut)
def trigger_retrain(
    force: bool = Query(False, description="Force retrain навіть якщо недостатньо feedback"),
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """
    Запускає перенавчання моделі вручну.
    Доступ: тільки ADMIN.
    """
    should_train, new_count, reason = active_learning_service.should_retrain(db)

    if not should_train and not force:
        return TriggerRetrainOut(
            success=False, job_id=None, message=f"Retrain not needed: {reason}"
        )

    try:
        job = active_learning_service.train_model(db, training_type="MANUAL")

        # Автоматично активуємо якщо це краща модель
        current_active = (
            db.query(MLModelMetadata).filter(MLModelMetadata.is_active == True).first()
        )

        new_model = (
            db.query(MLModelMetadata).filter(MLModelMetadata.version == job.model_version).first()
        )

        if not current_active or (new_model.accuracy > current_active.accuracy):
            active_learning_service.activate_model(db, job.model_version)
            message = f"Model {job.model_version} trained and activated successfully!"
        else:
            message = f"Model {job.model_version} trained but not activated (accuracy not better)"

        return TriggerRetrainOut(success=True, job_id=job.id, message=message)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Training failed: {str(e)}")


@router.get("/models", response_model=List[MLModelMetadataOut])
def list_models(
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """
    Список всіх ML моделей з метриками.
    Доступ: тільки ADMIN.
    """
    models = (
        db.query(MLModelMetadata).order_by(MLModelMetadata.created_at.desc()).limit(limit).all()
    )

    return models


@router.get("/models/{version}", response_model=MLModelMetadataOut)
def get_model(
    version: str,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """
    Отримати деталі конкретної моделі.
    Доступ: тільки ADMIN.
    """
    model = db.query(MLModelMetadata).filter(MLModelMetadata.version == version).first()

    if not model:
        raise HTTPException(status_code=404, detail=f"Model {version} not found")

    return model


@router.post("/models/{version}/activate", response_model=ActivateModelOut)
def activate_model(
    version: str,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """
    Активує певну версію моделі (робить її поточною).
    Доступ: тільки ADMIN.
    """
    try:
        success = active_learning_service.activate_model(db, version)

        if success:
            return ActivateModelOut(
                success=True, message=f"Model {version} activated successfully"
            )
        else:
            return ActivateModelOut(
                success=False, message=f"Failed to activate model {version}"
            )

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Activation failed: {str(e)}")


@router.get("/jobs", response_model=List[MLTrainingJobOut])
def list_training_jobs(
    limit: int = Query(20, ge=1, le=100),
    status: Optional[str] = Query(None, description="Filter by status: RUNNING, COMPLETED, FAILED"),
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """
    Список всіх training jobs (історія навчань).
    Доступ: тільки ADMIN.
    """
    query = db.query(MLTrainingJob).order_by(MLTrainingJob.started_at.desc())

    if status:
        query = query.filter(MLTrainingJob.status == status.upper())

    jobs = query.limit(limit).all()

    return jobs


@router.get("/jobs/{job_id}", response_model=MLTrainingJobOut)
def get_training_job(
    job_id: int,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """
    Отримати деталі конкретного training job.
    Доступ: тільки ADMIN.
    """
    job = db.query(MLTrainingJob).filter(MLTrainingJob.id == job_id).first()

    if not job:
        raise HTTPException(status_code=404, detail=f"Training job {job_id} not found")

    return job
