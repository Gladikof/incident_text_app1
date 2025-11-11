"""
SystemSettings model (singleton)
"""
from datetime import datetime
from sqlalchemy import Column, Integer, Boolean, Float, DateTime, Enum as SQLEnum
from sqlalchemy.orm import validates

from app.database import Base
from app.core.enums import MLModeEnum, VisibilityScopeEnum


class SystemSettings(Base):
    """
    Системні налаштування (singleton таблиця - завжди 1 запис з id=1)
    """
    __tablename__ = "system_settings"

    id = Column(Integer, primary_key=True, default=1)

    # === ML налаштування ===
    feature_ml_enabled = Column(Boolean, default=True, nullable=False)
    ml_mode = Column(SQLEnum(MLModeEnum), default=MLModeEnum.RECOMMEND, nullable=False)
    ml_conf_threshold_priority = Column(Float, default=0.6, nullable=False)
    ml_conf_threshold_category = Column(Float, default=0.6, nullable=False)

    # === Налаштування агентів ===
    agents_can_self_assign = Column(Boolean, default=True, nullable=False)
    agent_visibility_scope = Column(SQLEnum(VisibilityScopeEnum), default=VisibilityScopeEnum.DEPT, nullable=False)

    # === Метадані ===
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    @validates('ml_conf_threshold_priority', 'ml_conf_threshold_category')
    def validate_threshold(self, key, value):
        """Переконатися, що пороги в межах [0, 1]"""
        if not (0 <= value <= 1):
            raise ValueError(f"{key} must be between 0 and 1")
        return value

    def __repr__(self):
        return f"<SystemSettings ml_enabled={self.feature_ml_enabled} mode={self.ml_mode}>"

    @classmethod
    def get_settings(cls, db):
        """Отримати поточні налаштування (або створити default)"""
        settings = db.query(cls).filter(cls.id == 1).first()
        if not settings:
            settings = cls(id=1)
            db.add(settings)
            db.commit()
            db.refresh(settings)
        return settings
