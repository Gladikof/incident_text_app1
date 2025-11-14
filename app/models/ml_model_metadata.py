"""
ML Model Metadata - зберігає версії моделей та їх метрики для A/B testing та versioning.
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, Text, JSON
from app.database import Base


class MLModelMetadata(Base):
    """
    Метадані ML моделі - версія, метрики, статус активності.
    Дозволяє відслідковувати покращення моделі та робити rollback при потребі.
    """
    __tablename__ = "ml_model_metadata"

    id = Column(Integer, primary_key=True, index=True)
    version = Column(String(50), unique=True, nullable=False, index=True)

    # Коли модель була навчена
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Метрики на validation set
    accuracy = Column(Float, nullable=True)
    precision_p1 = Column(Float, nullable=True)
    precision_p2 = Column(Float, nullable=True)
    precision_p3 = Column(Float, nullable=True)
    recall_p1 = Column(Float, nullable=True)
    recall_p2 = Column(Float, nullable=True)
    recall_p3 = Column(Float, nullable=True)
    f1_score = Column(Float, nullable=True)

    # Кількість тренувальних прикладів
    training_samples_count = Column(Integer, nullable=True)

    # Чи активна ця модель зараз
    is_active = Column(Boolean, default=False, nullable=False)

    # Шлях до файлу моделі
    model_file_path = Column(String(500), nullable=True)

    # Додаткова інформація (hyperparameters, training config)
    metadata_json = Column(JSON, nullable=True)

    # Нотатки про модель
    notes = Column(Text, nullable=True)


class MLTrainingJob(Base):
    """
    Історія тренувальних jobs - коли запускалось навчання, скільки тривало, чи успішно.
    """
    __tablename__ = "ml_training_jobs"

    id = Column(Integer, primary_key=True, index=True)

    # Час запуску та завершення
    started_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    completed_at = Column(DateTime, nullable=True)

    # Статус: RUNNING, COMPLETED, FAILED
    status = Column(String(20), default="RUNNING", nullable=False, index=True)

    # Версія моделі яка вийшла з цього job
    model_version = Column(String(50), nullable=True)

    # Скільки нових feedback records було використано
    new_feedback_count = Column(Integer, nullable=True)
    total_training_samples = Column(Integer, nullable=True)

    # Якщо failed - причина
    error_message = Column(Text, nullable=True)

    # Тип тренування: FULL, INCREMENTAL
    training_type = Column(String(20), default="INCREMENTAL", nullable=False)

    # Логи тренування
    training_logs = Column(Text, nullable=True)
