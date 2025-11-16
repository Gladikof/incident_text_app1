"""
ML Service - інтеграція ML/LLM пайплайна з базою даних.
"""
import re
from typing import Dict, Optional
from datetime import datetime

from sqlalchemy.orm import Session

from app.core.enums import PriorityEnum, CategoryEnum, TriageReasonEnum
from app.models.ml_log import MLPredictionLog
from app.models.settings import SystemSettings
from app.ml_model import ml_model
from app.llm_router import route_with_llm
from app.services.ensemble_service import ensemble_service


class MLService:
    """
    Сервіс для ML-класифікації тікетів та логування результатів.
    """

    @staticmethod
    def predict_ticket(
        title: str,
        description: str,
        db: Session,
        ticket_id: Optional[int] = None,
        skip_llm: bool = False,
    ) -> Dict:
        """
        Виконує гібридну класифікацію (ML + LLM) та повертає словник із результатами.
        """
        settings = MLService._get_settings(db)

        if not settings.feature_ml_enabled:
            return {
                "ml_enabled": False,
                "priority_ml_suggested": None,
                "priority_ml_confidence": None,
                "category_ml_suggested": None,
                "category_ml_confidence": None,
                "category_llm_suggested": None,
                "category_llm_confidence": None,
                "triage_required": True,
                "triage_reason": TriageReasonEnum.ML_DISABLED,
                "ml_model_version": None,
                "llm_result": None,
                "llm_skipped": skip_llm,
            }

        # --- LLM ---
        llm_result: Optional[dict] = None
        llm_priority: Optional[PriorityEnum] = None
        llm_priority_conf: Optional[float] = None
        llm_category: Optional[CategoryEnum] = None
        llm_category_conf: Optional[float] = None

        if not skip_llm:
            try:
                llm_result = route_with_llm(title, description)
                if llm_result:
                    llm_priority = MLService._map_llm_priority(llm_result.get("priority"))
                    llm_priority_conf = 0.8 if llm_priority else None
                    llm_category = MLService._map_category(llm_result.get("category"))
                    llm_category_conf = 0.8 if llm_category else None
            except Exception as exc:
                print(f"[ML] LLM routing error: {exc}")
                llm_result = None

        # --- ML ---
        priority_ml: Optional[PriorityEnum] = None
        priority_conf: Optional[float] = None
        category_ml: Optional[CategoryEnum] = None
        category_conf: Optional[float] = None
        ml_model_version: Optional[str] = None

        text_blob = f"{title}\n{description}".strip()
        text_quality = MLService._check_text_quality(title, description)
        if text_blob:
            if ml_model.model is not None:
                try:
                    ml_label, ml_conf = ml_model.predict_priority(text_blob)
                    priority_ml = MLService._map_priority(ml_label)
                    priority_conf = float(ml_conf)
                    ml_model_version = getattr(ml_model, "version", "1.0")
                except Exception as exc:
                    print(f"[ML] Priority prediction error: {exc}")
            if getattr(ml_model, "category_model", None) is not None:
                try:
                    cat_label, cat_conf = ml_model.predict_category(text_blob)
                    category_ml = MLService._map_category(cat_label)
                    category_conf = float(cat_conf)
                except Exception as exc:
                    print(f"[ML] Category prediction error: {exc}")

        # --- Ensembles ---
        (
            ensemble_priority,
            ensemble_confidence,
            triage_required,
            triage_reason,
            ensemble_reasoning,
        ) = ensemble_service.combine_predictions(
            ml_priority=priority_ml,
            ml_confidence=priority_conf,
            llm_priority=llm_priority,
            llm_confidence=llm_priority_conf,
        )

        (
            category_ensemble,
            category_ensemble_confidence,
            category_ensemble_strategy,
            category_ensemble_reasoning,
        ) = ensemble_service.combine_categories(
            ml_category=category_ml,
            ml_confidence=category_conf,
            llm_category=llm_category,
            llm_confidence=llm_category_conf,
        )

        quality_note: Optional[str] = None
        if not text_quality["is_meaningful"]:
            triage_required = True
            triage_reason = TriageReasonEnum.MANUAL_FLAG
            quality_note = text_quality["reason"]
            if ensemble_reasoning:
                ensemble_reasoning = f"{ensemble_reasoning} | text_quality={quality_note}"
            else:
                ensemble_reasoning = f"text_quality={quality_note}"

        ensemble_stats = ensemble_service.get_strategy_stats(
            ml_priority=priority_ml,
            ml_confidence=priority_conf,
            llm_priority=llm_priority,
            llm_confidence=llm_priority_conf,
        )

        # --- Logging ---
        if ticket_id:
            notes_value = []
            if llm_result:
                notes_value.append(str(llm_result))
            if quality_note:
                notes_value.append(f"text_quality={quality_note}")
            combined_notes = " | ".join(notes_value) if notes_value else None

            log_entry = MLPredictionLog(
                ticket_id=ticket_id,
                model_version=ml_model_version or "unknown",
                priority_predicted=priority_ml,
                priority_confidence=priority_conf,
                priority_llm_predicted=llm_priority,
                priority_llm_confidence=llm_priority_conf,
                category_predicted=category_ml,
                category_confidence=category_conf,
                category_llm_predicted=llm_category,
                category_llm_confidence=llm_category_conf,
                ensemble_priority=ensemble_priority,
                ensemble_confidence=ensemble_confidence,
                ensemble_strategy=ensemble_stats.get("strategy_used") if priority_ml or llm_priority else None,
                ensemble_reasoning=ensemble_reasoning,
                ensemble_category=category_ensemble,
                ensemble_category_confidence=category_ensemble_confidence,
                ensemble_category_strategy=category_ensemble_strategy,
                ensemble_category_reasoning=category_ensemble_reasoning,
                triage_reason=triage_reason,
                input_text=text_blob,
                notes=combined_notes,
            )
            db.add(log_entry)
            db.commit()

        return {
            "ml_enabled": True,
            "priority_ml_suggested": priority_ml,
            "priority_ml_confidence": priority_conf,
            "priority_llm_suggested": llm_priority,
            "priority_llm_confidence": llm_priority_conf,
            "priority_ensemble": ensemble_priority,
            "ensemble_confidence": ensemble_confidence,
            "ensemble_strategy": ensemble_stats.get("strategy_used") if priority_ml or llm_priority else None,
            "ensemble_reasoning": ensemble_reasoning,
            "category_ml_suggested": category_ml,
            "category_ml_confidence": category_conf,
            "category_llm_suggested": llm_category,
            "category_llm_confidence": llm_category_conf,
            "category_ensemble": category_ensemble,
            "category_ensemble_confidence": category_ensemble_confidence,
            "category_ensemble_strategy": category_ensemble_strategy,
            "category_ensemble_reasoning": category_ensemble_reasoning,
            "triage_required": triage_required,
            "triage_reason": triage_reason,
            "ml_model_version": ml_model_version,
            "llm_result": llm_result,
            "llm_skipped": skip_llm,
            "text_quality_flag": quality_note,
        }

    @staticmethod
    def _get_settings(db: Session) -> SystemSettings:
        settings = db.query(SystemSettings).filter(SystemSettings.id == 1).first()
        if not settings:
            settings = SystemSettings(id=1)
            db.add(settings)
            db.commit()
            db.refresh(settings)
        return settings

    @staticmethod
    def _map_priority(ml_label: str) -> Optional[PriorityEnum]:
        mapping = {
            "high": PriorityEnum.P1,
            "medium": PriorityEnum.P2,
            "low": PriorityEnum.P3,
        }
        return mapping.get((ml_label or "").lower())

    @staticmethod
    def _map_llm_priority(llm_label: Optional[str]) -> Optional[PriorityEnum]:
        if not llm_label:
            return None
        mapping = {
            "P1": PriorityEnum.P1,
            "P2": PriorityEnum.P2,
            "P3": PriorityEnum.P3,
        }
        return mapping.get(llm_label.upper())

    @staticmethod
    def _map_category(label: Optional[str]) -> Optional[CategoryEnum]:
        if not label:
            return None
        mapping = {
            "hardware": CategoryEnum.HARDWARE,
            "software": CategoryEnum.SOFTWARE,
            "network": CategoryEnum.NETWORK,
            "access": CategoryEnum.ACCESS,
            "other": CategoryEnum.OTHER,
            "workstation": CategoryEnum.HARDWARE,
        }
        return mapping.get(label.lower(), CategoryEnum.OTHER)

    @staticmethod
    def _check_text_quality(title: Optional[str], description: Optional[str]) -> Dict[str, Optional[str]]:
        """
        Simple heuristic detection for meaningless tickets.
        """
        text = f"{title or ''} {description or ''}".strip()
        normalized = re.sub(r"\s+", " ", text)
        if not normalized:
            return {"is_meaningful": False, "reason": "empty_text"}

        if len(normalized) < 30:
            return {"is_meaningful": False, "reason": "too_short"}

        words = [w for w in re.split(r"[^\w]+", normalized) if w]
        if len(words) < 4:
            return {"is_meaningful": False, "reason": "too_few_words"}

        alpha_chars = sum(1 for ch in normalized if ch.isalpha())
        if not alpha_chars or (alpha_chars / len(normalized)) < 0.5:
            return {"is_meaningful": False, "reason": "low_alpha_ratio"}

        gibberish = {"test", "aaa", "ffff", "lorem", "asdf", "na", "null"}
        if words and all(word.lower() in gibberish for word in words):
            return {"is_meaningful": False, "reason": "gibberish"}

        return {"is_meaningful": True, "reason": None}


ml_service = MLService()
