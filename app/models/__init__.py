"""
ORM Models
"""
from app.models.user import User
from app.models.department import Department
from app.models.asset import Asset
from app.models.ticket import Ticket
from app.models.comment import TicketComment
from app.models.ml_log import MLPredictionLog
from app.models.settings import SystemSettings

__all__ = [
    "User",
    "Department",
    "Asset",
    "Ticket",
    "TicketComment",
    "MLPredictionLog",
    "SystemSettings",
]
