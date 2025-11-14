"""
Enums для системи Service Desk
"""
import enum


class RoleEnum(str, enum.Enum):
    """Ролі користувачів"""
    ADMIN = "ADMIN"
    LEAD = "LEAD"
    AGENT = "AGENT"
    USER = "USER"


class StatusEnum(str, enum.Enum):
    """Статуси тікетів"""
    NEW = "NEW"
    TRIAGE = "TRIAGE"
    IN_PROGRESS = "IN_PROGRESS"
    RESOLVED = "RESOLVED"
    CLOSED = "CLOSED"


class PriorityEnum(str, enum.Enum):
    """Пріоритети тікетів"""
    P1 = "P1"  # Критичний
    P2 = "P2"  # Високий
    P3 = "P3"  # Стандартний


class CategoryEnum(str, enum.Enum):
    """Категорії тікетів"""
    HARDWARE = "Hardware"
    SOFTWARE = "Software"
    NETWORK = "Network"
    ACCESS = "Access"
    OTHER = "Other"


class TriageReasonEnum(str, enum.Enum):
    """Причини тріажу"""
    LOW_PRIORITY_CONF = "LOW_PRIORITY_CONF"
    LOW_CATEGORY_CONF = "LOW_CATEGORY_CONF"
    ML_DISABLED = "ML_DISABLED"
    MANUAL_FLAG = "MANUAL_FLAG"
    LLM_PRIORITY_MISMATCH = "LLM_PRIORITY_MISMATCH"


class MLModeEnum(str, enum.Enum):
    """Режими роботи ML"""
    RECOMMEND = "RECOMMEND"  # Рекомендації, не застосовувати автоматично
    AUTO_APPLY = "AUTO_APPLY"  # Автоматичне застосування при високій впевненості


class VisibilityScopeEnum(str, enum.Enum):
    """Обсяг видимості тікетів для агентів"""
    DEPT = "DEPT"  # Тільки свій департамент
    ALL = "ALL"  # Всі департаменти
