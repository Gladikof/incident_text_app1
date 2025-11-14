"""
Active Learning Service ? manage retraining of priority and category ML models
based on feedback from agents.
"""
from __future__ import annotations

import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import joblib
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import SGDClassifier
from sklearn.metrics import accuracy_score, precision_recall_fscore_support
from sklearn.model_selection import train_test_split
from sqlalchemy.orm import Session

from app.config import settings
from app.core.enums import CategoryEnum, PriorityEnum
from app.models.ml_log import MLPredictionLog
from app.models.ml_model_metadata import MLModelMetadata, MLTrainingJob


class ActiveLearningService:
    """Facade over ML retraining logic for priorities and categories."""

    MIN_NEW_FEEDBACK_FOR_RETRAIN = 50
    MIN_TOTAL_SAMPLES = 100
    MIN_CATEGORY_SAMPLES = 40

    def __init__(self) -> None:
        self.artifacts_dir = Path(settings.BASE_DIR) / "artifacts"
        self.artifacts_dir.mkdir(parents=True, exist_ok=True)

    def should_retrain(self, db: Session) -> Tuple[bool, int, str]:
        last_job = (
            db.query(MLTrainingJob)
            .filter(MLTrainingJob.status == "COMPLETED")
            .order_by(MLTrainingJob.completed_at.desc())
            .first()
        )

        if not last_job:
            total_feedback = (
                db.query(MLPredictionLog)
                .filter(MLPredictionLog.priority_final.isnot(None))
                .count()
            )
            if total_feedback >= self.MIN_TOTAL_SAMPLES:
                return True, total_feedback, "Initial training ? enough samples"
            return False, total_feedback, (
                f"Not enough samples for initial training "
                f"({total_feedback}/{self.MIN_TOTAL_SAMPLES})"
            )

        new_feedback = (
            db.query(MLPredictionLog)
            .filter(
                MLPredictionLog.priority_final.isnot(None),
                MLPredictionLog.priority_feedback_recorded_at > last_job.completed_at,
            )
            .count()
        )
        if new_feedback >= self.MIN_NEW_FEEDBACK_FOR_RETRAIN:
            return True, new_feedback, f"Accumulated {new_feedback} new feedback entries"
        return (
            False,
            new_feedback,
            f"Not enough new feedback ({new_feedback}/{self.MIN_NEW_FEEDBACK_FOR_RETRAIN})",
        )

    def get_training_data(
        self,
        db: Session,
        use_tickets: bool = False,
    ) -> Tuple[List[str], List[str], List[Optional[str]]]:
        texts: List[str] = []
        priority_labels: List[str] = []
        category_labels: List[Optional[str]] = []

        def append_sample(
            text: Optional[str],
            priority: Optional[PriorityEnum],
            category: Optional[CategoryEnum],
        ) -> None:
            if not text or not priority:
                return
            cleaned = text.strip()
            if not cleaned:
                return
            texts.append(cleaned)

            priority_labels.append(
                "high" if priority == PriorityEnum.P1 else
                "medium" if priority == PriorityEnum.P2 else
                "low"
            )

            if category is None:
                category_labels.append(None)
            elif isinstance(category, CategoryEnum):
                category_labels.append(category.value)
            else:
                category_labels.append(str(category))

        if use_tickets:
            from app.models.ticket import Ticket

            tickets = (
                db.query(Ticket)
                .filter(
                    Ticket.priority_manual.isnot(None),
                    Ticket.title.isnot(None),
                    Ticket.description.isnot(None),
                )
                .all()
            )
            for ticket in tickets:
                append_sample(
                    f"{ticket.title}\n{ticket.description}",
                    ticket.priority_manual,
                    ticket.category,
                )
            return texts, priority_labels, category_labels

        logs = (
            db.query(MLPredictionLog)
            .filter(
                MLPredictionLog.input_text.isnot(None),
                MLPredictionLog.priority_final.isnot(None),
            )
            .all()
        )
        for log in logs:
            append_sample(log.input_text, log.priority_final, log.category_final)
        return texts, priority_labels, category_labels

    def train_model(self, db: Session, training_type: str = "INCREMENTAL") -> MLTrainingJob:
        job = MLTrainingJob(started_at=datetime.utcnow(), status="RUNNING", training_type=training_type)
        db.add(job)
        db.commit()
        db.refresh(job)

        try:
            use_tickets = training_type == "INITIAL"
            texts, priority_labels, category_labels = self.get_training_data(
                db, use_tickets=use_tickets
            )

            if len(texts) < self.MIN_TOTAL_SAMPLES:
                raise ValueError(
                    f"Not enough training samples: {len(texts)}/{self.MIN_TOTAL_SAMPLES}"
                )

            X_train, X_val, y_train, y_val = train_test_split(
                texts, priority_labels, test_size=0.2, random_state=42, stratify=priority_labels
            )

            vectorizer = TfidfVectorizer(max_features=5000, ngram_range=(1, 2))
            X_train_vec = vectorizer.fit_transform(X_train)
            X_val_vec = vectorizer.transform(X_val)

            model = SGDClassifier(loss="log_loss", max_iter=1000, class_weight="balanced", random_state=42)
            model.fit(X_train_vec, y_train)

            y_pred = model.predict(X_val_vec)
            accuracy = accuracy_score(y_val, y_pred)
            precision, recall, f1, _ = precision_recall_fscore_support(
                y_val, y_pred, labels=["high", "medium", "low"], zero_division=0
            )

            metrics = {
                "accuracy": float(accuracy),
                "precision_p1": float(precision[0]),
                "precision_p2": float(precision[1]),
                "precision_p3": float(precision[2]),
                "recall_p1": float(recall[0]),
                "recall_p2": float(recall[1]),
                "recall_p3": float(recall[2]),
                "f1_score": float(np.mean(f1)),
            }

            version = datetime.utcnow().strftime("v%Y%m%d_%H%M%S")
            model_path = self.artifacts_dir / f"model_pri_text_{version}.joblib"
            joblib.dump({"model": model, "vectorizer": vectorizer}, model_path)

            category_model_info = None
            if len([lbl for lbl in category_labels if lbl]) >= self.MIN_CATEGORY_SAMPLES:
                category_model_info = self._train_category_classifier(texts, category_labels, version)

            metadata_json = {
                "train_size": len(X_train),
                "val_size": len(X_val),
                "class_distribution": {
                    "high": int(priority_labels.count("high")),
                    "medium": int(priority_labels.count("medium")),
                    "low": int(priority_labels.count("low")),
                },
            }
            if category_model_info:
                metadata_json["category_model"] = category_model_info

            model_metadata = MLModelMetadata(
                version=version,
                created_at=datetime.utcnow(),
                accuracy=metrics["accuracy"],
                precision_p1=metrics["precision_p1"],
                precision_p2=metrics["precision_p2"],
                precision_p3=metrics["precision_p3"],
                recall_p1=metrics["recall_p1"],
                recall_p2=metrics["recall_p2"],
                recall_p3=metrics["recall_p3"],
                f1_score=metrics["f1_score"],
                training_samples_count=len(texts),
                is_active=False,
                model_file_path=str(model_path),
                metadata_json=metadata_json,
                notes=f"Trained via {training_type} on {len(texts)} samples",
            )
            db.add(model_metadata)

            job.status = "COMPLETED"
            job.completed_at = datetime.utcnow()
            job.model_version = version
            job.total_training_samples = len(texts)
            extra = ""
            if category_model_info:
                extra = f" | Category model accuracy: {category_model_info['accuracy']:.3f}"
            job.training_logs = f"Training completed successfully. Metrics: {metrics}{extra}"

            db.commit()
            return job

        except Exception as exc:
            job.status = "FAILED"
            job.completed_at = datetime.utcnow()
            job.error_message = str(exc)
            db.commit()
            raise

    def activate_model(self, db: Session, version: str) -> bool:
        db.query(MLModelMetadata).update({"is_active": False})
        model = db.query(MLModelMetadata).filter(MLModelMetadata.version == version).first()
        if not model:
            raise ValueError(f"Model {version} not found")

        model.is_active = True
        db.commit()

        copied = False
        priority_target = self.artifacts_dir / "model_pri_text.joblib"
        if os.path.exists(model.model_file_path):
            from shutil import copy2

            copy2(model.model_file_path, priority_target)
            copied = True

        metadata = model.metadata_json if isinstance(model.metadata_json, dict) else {}
        category_info = metadata.get("category_model") if metadata else None
        if category_info and category_info.get("file_path"):
            from shutil import copy2
            cat_src = Path(category_info["file_path"])
            if cat_src.exists():
                copy2(cat_src, self.artifacts_dir / "model_cat_text.joblib")

        return copied

    def get_best_model(self, db: Session) -> Optional[MLModelMetadata]:
        return (
            db.query(MLModelMetadata)
            .filter(MLModelMetadata.accuracy.isnot(None))
            .order_by(MLModelMetadata.accuracy.desc())
            .first()
        )

    def auto_retrain_if_needed(self, db: Session) -> Optional[MLTrainingJob]:
        should_train, _, reason = self.should_retrain(db)
        print(f"[ActiveLearning] Retrain check: {reason}")
        if not should_train:
            return None
        return self.train_model(db, training_type="INCREMENTAL")

    def _train_category_classifier(
        self, texts: List[str], labels: List[Optional[str]], version: str
    ) -> Dict[str, any]:
        samples = [
            (text.strip(), label)
            for text, label in zip(texts, labels)
            if text and label
        ]
        if len(samples) < self.MIN_CATEGORY_SAMPLES:
            raise ValueError(
                f"Not enough category samples: {len(samples)}/{self.MIN_CATEGORY_SAMPLES}"
            )

        cat_texts, cat_labels = zip(*samples)
        X_train, X_val, y_train, y_val = train_test_split(
            cat_texts, cat_labels, test_size=0.2, random_state=42, stratify=cat_labels
        )

        vectorizer = TfidfVectorizer(max_features=4000, ngram_range=(1, 2))
        X_train_vec = vectorizer.fit_transform(X_train)
        X_val_vec = vectorizer.transform(X_val)

        model = SGDClassifier(
            loss="log_loss", max_iter=1000, class_weight="balanced", random_state=42
        )
        model.fit(X_train_vec, y_train)

        y_pred = model.predict(X_val_vec)
        accuracy = accuracy_score(y_val, y_pred)
        precision, recall, f1, _ = precision_recall_fscore_support(
            y_val, y_pred, labels=sorted(set(cat_labels)), zero_division=0
        )

        model_path = self.artifacts_dir / f"model_cat_text_{version}.joblib"
        joblib.dump({"model": model, "vectorizer": vectorizer}, model_path)

        return {
            "file_path": str(model_path),
            "samples": len(cat_labels),
            "accuracy": float(accuracy),
            "f1_score": float(np.mean(f1)),
        }

active_learning_service = ActiveLearningService()

