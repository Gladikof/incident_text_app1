"""
ML Service - інтеграція існуючих ML моделей з новою базою даних.
Відповідає за виклик ML/LLM пайплайну та логування результатів.
"""
from typing import Dict, Optional, Tuple
from datetime import datetime

from sqlalchemy.orm import Session

from app.core.enums import PriorityEnum, CategoryEnum, TriageReasonEnum, MLModeEnum
from app.models.ticket import Ticket
from app.models.ml_log import MLPredictionLog
from app.models.settings import SystemSettings
from app.ml_model import ml_model
from app.llm_router import route_with_llm
from app.services.ensemble_service import ensemble_service


class MLService:
    """
    Сервіс для ML-класифікації тікетів.
    """

    @staticmethod
    def predict_ticket(
        title: str,
        description: str,
        db: Session,
        ticket_id: Optional[int] = None,
    ) -> Dict:
        """
        Виконує ML-класифікацію тікета:
        1. LLM класифікація (category, priority, urgency, team, assignee)
        2. ML текстова модель (priority prediction)
        3. Порівняння з порогами впевненості
        4. Логування результатів

        Args:
            title: Заголовок тікета
            description: Опис тікета
            db: Database session
            ticket_id: ID тікета (якщо вже створений)

        Returns:
            Dict з ML predictions та metadata
        """
        settings = MLService._get_settings(db)

        # Якщо ML вимкнено
        if not settings.feature_ml_enabled:
            return {
                "ml_enabled": False,
                "priority_ml_suggested": None,
                "priority_ml_confidence": None,
                "category_ml_suggested": None,
                "category_ml_confidence": None,
                "triage_required": True,
                "triage_reason": TriageReasonEnum.ML_DISABLED,
                "ml_model_version": None,
            }

        # 1. LLM класифікація
        llm_result = None
        category_ml = None
        category_conf = None

        try:
            llm_result = route_with_llm(title, description)
            # llm_result містить: category, priority, urgency, team, assignee
            category_ml = MLService._map_category(llm_result.get("category"))
            # Припускаємо, що LLM має високу впевненість (0.8)
            category_conf = 0.8
        except Exception as e:
            print(f"[ML] LLM routing error: {e}")
            category_ml = None
            category_conf = None

        # 2. ML модель для пріоритету
        priority_ml = None
        priority_conf = None
        ml_model_version = None

        full_text = f"{title}\n{description}".strip()
        if full_text and ml_model.model is not None:
            try:
                ml_label, ml_conf = ml_model.predict_priority(full_text)
                # ml_label: "high", "medium", "low"
                priority_ml = MLService._map_priority(ml_label)
                priority_conf = float(ml_conf)
                ml_model_version = getattr(ml_model, "version", "1.0")
            except Exception as e:
                print(f"[ML] Priority prediction error: {e}")
                priority_ml = None
                priority_conf = None

        # 3. LLM priority (витягуємо з llm_result)
        llm_priority_ml = None
        llm_priority_conf = None
        if llm_result and llm_result.get("priority"):
            llm_priority_str = llm_result.get("priority")  # "P1", "P2", "P3"
            llm_priority_ml = MLService._map_llm_priority(llm_priority_str)
            # Припускаємо високу впевненість для LLM (0.8)
            llm_priority_conf = 0.8

        # 4. ENSEMBLE DECISION - комбінуємо ML та LLM predictions
        (
            ensemble_priority,
            ensemble_confidence,
            triage_required,
            triage_reason,
            ensemble_reasoning
        ) = ensemble_service.combine_predictions(
            ml_priority=priority_ml,
            ml_confidence=priority_conf,
            llm_priority=llm_priority_ml,
            llm_confidence=llm_priority_conf
        )

        # Отримуємо додаткову статистику
        ensemble_stats = ensemble_service.get_strategy_stats(
            ml_priority=priority_ml,
            ml_confidence=priority_conf,
            llm_priority=llm_priority_ml,
            llm_confidence=llm_priority_conf
        )

        # Перевіряємо category confidence
        if category_conf is not None and category_conf < settings.ml_conf_threshold_category:
            if not triage_required:  # Якщо ще не потрібен
                triage_required = True
                triage_reason = TriageReasonEnum.LOW_CATEGORY_CONF

        # 5. Логування результатів
        if ticket_id:
            log_entry = MLPredictionLog(
                ticket_id=ticket_id,
                model_version=ml_model_version or "unknown",
                # ML predictions
                priority_predicted=priority_ml,
                priority_confidence=priority_conf,
                # LLM predictions
                priority_llm_predicted=llm_priority_ml,
                priority_llm_confidence=llm_priority_conf,
                # Category
                category_predicted=category_ml,
                category_confidence=category_conf,
                # Ensemble decision
                ensemble_priority=ensemble_priority,
                ensemble_confidence=ensemble_confidence,
                ensemble_strategy=ensemble_stats.get("strategy_used"),
                ensemble_reasoning=ensemble_reasoning,
                # Triage
                triage_reason=triage_reason,
                # Other
                input_text=f"{title}\n{description}",
                notes=str(llm_result) if llm_result else None,
            )
            db.add(log_entry)
            db.commit()

        return {
            "ml_enabled": True,
            # ML predictions
            "priority_ml_suggested": priority_ml,
            "priority_ml_confidence": priority_conf,
            # LLM predictions
            "priority_llm_suggested": llm_priority_ml,
            "priority_llm_confidence": llm_priority_conf,
            # ENSEMBLE decision (основне рішення!)
            "priority_ensemble": ensemble_priority,
            "ensemble_confidence": ensemble_confidence,
            "ensemble_strategy": ensemble_stats.get("strategy_used"),
            "ensemble_reasoning": ensemble_reasoning,
            # Category
            "category_ml_suggested": category_ml,
            "category_ml_confidence": category_conf,
            # Triage
            "triage_required": triage_required,
            "triage_reason": triage_reason,
            # Other
            "ml_model_version": ml_model_version,
            "llm_result": llm_result,  # Додаткові дані (team, assignee тощо)
        }

    @staticmethod
    def _get_settings(db: Session) -> SystemSettings:
        """Отримує системні налаштування (singleton)."""
        settings = db.query(SystemSettings).filter(SystemSettings.id == 1).first()
        if not settings:
            # Створюємо дефолтні налаштування
            settings = SystemSettings(id=1)
            db.add(settings)
            db.commit()
            db.refresh(settings)
        return settings

    @staticmethod
    def _map_priority(ml_label: str) -> Optional[PriorityEnum]:
        """Маппінг ML labels (high/medium/low) -> PriorityEnum (P1/P2/P3)."""
        mapping = {
            "high": PriorityEnum.P1,
            "medium": PriorityEnum.P2,
            "low": PriorityEnum.P3,
        }
        return mapping.get(ml_label.lower())

    @staticmethod
    def _map_llm_priority(llm_label: str) -> Optional[PriorityEnum]:
        """Маппінг LLM priority labels (P1/P2/P3) -> PriorityEnum."""
        if not llm_label:
            return None
        mapping = {
            "P1": PriorityEnum.P1,
            "P2": PriorityEnum.P2,
            "P3": PriorityEnum.P3,
        }
        return mapping.get(llm_label.upper())

    @staticmethod
    def _map_category(llm_category: Optional[str]) -> Optional[CategoryEnum]:
        """Маппінг LLM категорій -> CategoryEnum."""
        if not llm_category:
            return None

        # Припускаємо, що LLM повертає категорії як в CategoryEnum
        # Або робимо маппінг
        mapping = {
            "hardware": CategoryEnum.HARDWARE,
            "software": CategoryEnum.SOFTWARE,
            "network": CategoryEnum.NETWORK,
            "access": CategoryEnum.ACCESS,
            "other": CategoryEnum.OTHER,
            "workstation": CategoryEnum.HARDWARE,  # LLM може повернути "Workstation"
        }
        return mapping.get(llm_category.lower(), CategoryEnum.OTHER)


ml_service = MLService()
