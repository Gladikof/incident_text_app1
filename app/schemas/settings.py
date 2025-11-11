"""
System Settings schemas
"""
from datetime import datetime
from pydantic import BaseModel, Field, validator

from app.core.enums import MLModeEnum, VisibilityScopeEnum


class SystemSettingsBase(BaseModel):
    """Базові налаштування"""
    feature_ml_enabled: bool = True
    ml_mode: MLModeEnum = MLModeEnum.RECOMMEND
    ml_conf_threshold_priority: float = Field(0.6, ge=0.0, le=1.0)
    ml_conf_threshold_category: float = Field(0.6, ge=0.0, le=1.0)
    agents_can_self_assign: bool = True
    agent_visibility_scope: VisibilityScopeEnum = VisibilityScopeEnum.DEPT


class SystemSettingsUpdate(BaseModel):
    """Оновлення налаштувань"""
    feature_ml_enabled: bool | None = None
    ml_mode: MLModeEnum | None = None
    ml_conf_threshold_priority: float | None = Field(None, ge=0.0, le=1.0)
    ml_conf_threshold_category: float | None = Field(None, ge=0.0, le=1.0)
    agents_can_self_assign: bool | None = None
    agent_visibility_scope: VisibilityScopeEnum | None = None


class SystemSettingsOut(SystemSettingsBase):
    """Налаштування для відповіді"""
    id: int
    updated_at: datetime

    class Config:
        from_attributes = True
