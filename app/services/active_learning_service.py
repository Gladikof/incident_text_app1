"""
Active Learning Service - автоматичне перенавчання ML моделі на основі нових feedback.

Основна ідея:
1. Відслідковуємо кількість нових feedback records
2. Коли набирається достатньо (наприклад, 50) - автоматично запускаємо retraining
3. Зберігаємо метрики нової моделі
4. Якщо нова модель краща - активуємо її
"""
import os
import joblib
import numpy as np
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, Tuple, Dict
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import SGDClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, precision_recall_fscore_support
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.ml_log import MLPredictionLog
from app.models.ml_model_metadata import MLModelMetadata, MLTrainingJob
from app.core.enums import PriorityEnum
from app.config import settings


class ActiveLearningService:
    """
    Сервіс для автоматичного навчання ML моделі.
    """

    # Мінімальна кількість нових feedback для тригера retraining
    MIN_NEW_FEEDBACK_FOR_RETRAIN = 50

    # Мінімальна кількість всього samples для навчання
    MIN_TOTAL_SAMPLES = 100

    def __init__(self):
        self.artifacts_dir = Path(settings.BASE_DIR) / "artifacts"
        self.artifacts_dir.mkdir(exist_ok=True)

    def should_retrain(self, db: Session) -> Tuple[bool, int, str]:
        """
        Перевіряє чи потрібно перенавчувати модель.

        Returns:
            (should_retrain: bool, new_feedback_count: int, reason: str)
        """
        # Знайти останній успішний training job
        last_job = (
            db.query(MLTrainingJob)
            .filter(MLTrainingJob.status == "COMPLETED")
            .order_by(MLTrainingJob.completed_at.desc())
            .first()
        )

        # Якщо ніколи не навчалась - треба навчити
        if not last_job:
            total_feedback = (
                db.query(MLPredictionLog)
                .filter(MLPredictionLog.priority_final.isnot(None))
                .count()
            )

            if total_feedback >= self.MIN_TOTAL_SAMPLES:
                return True, total_feedback, "Initial training - never trained before"
            else:
                return (
                    False,
                    total_feedback,
                    f"Not enough samples for initial training ({total_feedback}/{self.MIN_TOTAL_SAMPLES})",
                )

        # Порахувати нові feedback з моменту останнього тренування
        last_training_time = last_job.completed_at

        new_feedback_count = (
            db.query(MLPredictionLog)
            .filter(
                MLPredictionLog.priority_final.isnot(None),
                MLPredictionLog.priority_feedback_recorded_at > last_training_time,
            )
            .count()
        )

        if new_feedback_count >= self.MIN_NEW_FEEDBACK_FOR_RETRAIN:
            return (
                True,
                new_feedback_count,
                f"Accumulated {new_feedback_count} new feedback records",
            )

        return (
            False,
            new_feedback_count,
            f"Not enough new feedback ({new_feedback_count}/{self.MIN_NEW_FEEDBACK_FOR_RETRAIN})",
        )

    def get_training_data(
        self, db: Session, since_date: Optional[datetime] = None
    ) -> Tuple[list, list]:
        """
        Витягує тренувальні дані з БД.

        Args:
            db: Database session
            since_date: Якщо вказано - бере тільки feedback після цієї дати

        Returns:
            (texts: list[str], labels: list[str])
        """
        query = db.query(MLPredictionLog).filter(
            MLPredictionLog.priority_final.isnot(None), MLPredictionLog.input_text.isnot(None)
        )

        if since_date:
            query = query.filter(MLPredictionLog.priority_feedback_recorded_at > since_date)

        logs = query.all()

        texts = []
        labels = []

        for log in logs:
            if not log.input_text or not log.priority_final:
                continue

            texts.append(log.input_text.strip())

            # Конвертуємо PriorityEnum -> str label для ML
            priority = log.priority_final
            if priority == PriorityEnum.P1:
                labels.append("high")
            elif priority == PriorityEnum.P2:
                labels.append("medium")
            elif priority == PriorityEnum.P3:
                labels.append("low")

        return texts, labels

    def train_model(self, db: Session, training_type: str = "INCREMENTAL") -> MLTrainingJob:
        """
        Навчає нову ML модель.

        Args:
            db: Database session
            training_type: "FULL" або "INCREMENTAL"

        Returns:
            MLTrainingJob record
        """
        # Створюємо job запис
        job = MLTrainingJob(
            started_at=datetime.utcnow(), status="RUNNING", training_type=training_type
        )
        db.add(job)
        db.commit()
        db.refresh(job)

        try:
            # Отримуємо всі тренувальні дані
            texts, labels = self.get_training_data(db)

            if len(texts) < self.MIN_TOTAL_SAMPLES:
                raise ValueError(
                    f"Not enough training samples: {len(texts)}/{self.MIN_TOTAL_SAMPLES}"
                )

            # Розбиваємо на train/validation
            X_train, X_val, y_train, y_val = train_test_split(
                texts, labels, test_size=0.2, random_state=42, stratify=labels
            )

            # Створюємо TF-IDF векторизатор
            vectorizer = TfidfVectorizer(max_features=5000, ngram_range=(1, 2))
            X_train_vec = vectorizer.fit_transform(X_train)
            X_val_vec = vectorizer.transform(X_val)

            # Навчаємо SGDClassifier (підтримує partial_fit для incremental learning)
            model = SGDClassifier(
                loss="log_loss",  # для probability estimates
                max_iter=1000,
                random_state=42,
                class_weight="balanced",  # для unbalanced datasets
            )
            model.fit(X_train_vec, y_train)

            # Обчислюємо метрики на validation set
            y_pred = model.predict(X_val_vec)
            accuracy = accuracy_score(y_val, y_pred)

            # Precision, recall, f1 для кожного класу
            precision, recall, f1, support = precision_recall_fscore_support(
                y_val, y_pred, labels=["high", "medium", "low"], zero_division=0
            )

            metrics = {
                "accuracy": float(accuracy),
                "precision_p1": float(precision[0]),  # high
                "precision_p2": float(precision[1]),  # medium
                "precision_p3": float(precision[2]),  # low
                "recall_p1": float(recall[0]),
                "recall_p2": float(recall[1]),
                "recall_p3": float(recall[2]),
                "f1_score": float(np.mean(f1)),
            }

            # Генеруємо версію моделі
            version = datetime.utcnow().strftime("v%Y%m%d_%H%M%S")

            # Зберігаємо модель + vectorizer разом
            model_path = self.artifacts_dir / f"model_pri_text_{version}.joblib"
            joblib.dump({"model": model, "vectorizer": vectorizer}, model_path)

            # Створюємо metadata запис
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
                is_active=False,  # Не активуємо автоматично
                model_file_path=str(model_path),
                metadata_json={
                    "train_size": len(X_train),
                    "val_size": len(X_val),
                    "class_distribution": {
                        "high": int(labels.count("high")),
                        "medium": int(labels.count("medium")),
                        "low": int(labels.count("low")),
                    },
                },
                notes=f"Trained via {training_type} on {len(texts)} samples",
            )
            db.add(model_metadata)

            # Оновлюємо job
            job.status = "COMPLETED"
            job.completed_at = datetime.utcnow()
            job.model_version = version
            job.total_training_samples = len(texts)
            job.training_logs = f"Training completed successfully. Metrics: {metrics}"

            db.commit()

            print(f"[ActiveLearning] Model {version} trained successfully!")
            print(f"[ActiveLearning] Accuracy: {metrics['accuracy']:.3f}")
            print(f"[ActiveLearning] F1-score: {metrics['f1_score']:.3f}")

            return job

        except Exception as e:
            # Якщо щось пішло не так
            job.status = "FAILED"
            job.completed_at = datetime.utcnow()
            job.error_message = str(e)
            db.commit()

            print(f"[ActiveLearning] Training failed: {e}")
            raise

    def activate_model(self, db: Session, version: str) -> bool:
        """
        Активує певну версію моделі (робить її поточною).

        Args:
            db: Database session
            version: Версія моделі для активації

        Returns:
            True if successful
        """
        # Деактивуємо всі моделі
        db.query(MLModelMetadata).update({"is_active": False})

        # Активуємо вибрану
        model = db.query(MLModelMetadata).filter(MLModelMetadata.version == version).first()

        if not model:
            raise ValueError(f"Model version {version} not found")

        model.is_active = True
        db.commit()

        # Копіюємо файл моделі як поточний
        current_model_path = self.artifacts_dir / "model_pri_text.joblib"
        if os.path.exists(model.model_file_path):
            import shutil

            shutil.copy(model.model_file_path, current_model_path)
            print(f"[ActiveLearning] Model {version} activated successfully!")
            return True

        return False

    def get_best_model(self, db: Session) -> Optional[MLModelMetadata]:
        """
        Знаходить модель з найкращою accuracy.

        Returns:
            MLModelMetadata або None
        """
        return (
            db.query(MLModelMetadata)
            .filter(MLModelMetadata.accuracy.isnot(None))
            .order_by(MLModelMetadata.accuracy.desc())
            .first()
        )

    def auto_retrain_if_needed(self, db: Session) -> Optional[MLTrainingJob]:
        """
        Перевіряє чи потрібно перенавчувати і робить це автоматично.

        Returns:
            MLTrainingJob якщо відбулось навчання, None якщо ні
        """
        should_train, new_count, reason = self.should_retrain(db)

        print(f"[ActiveLearning] Retrain check: {reason}")

        if not should_train:
            return None

        print(f"[ActiveLearning] Starting automatic retraining...")
        job = self.train_model(db, training_type="INCREMENTAL")

        # Автоматично активуємо якщо це перша модель або якщо нова краща
        current_active = (
            db.query(MLModelMetadata).filter(MLModelMetadata.is_active == True).first()
        )

        new_model = (
            db.query(MLModelMetadata).filter(MLModelMetadata.version == job.model_version).first()
        )

        if not current_active:
            # Перша модель - активуємо
            print(f"[ActiveLearning] Activating first model: {job.model_version}")
            self.activate_model(db, job.model_version)
        elif new_model.accuracy > current_active.accuracy:
            # Нова модель краща - активуємо
            print(
                f"[ActiveLearning] New model better ({new_model.accuracy:.3f} > {current_active.accuracy:.3f}), activating {job.model_version}"
            )
            self.activate_model(db, job.model_version)
        else:
            print(
                f"[ActiveLearning] New model not better ({new_model.accuracy:.3f} <= {current_active.accuracy:.3f}), keeping {current_active.version}"
            )

        return job


# Глобальний інстанс
active_learning_service = ActiveLearningService()
