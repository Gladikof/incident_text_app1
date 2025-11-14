"""
Ensemble Service - розумне комбінування ML та LLM predictions.

Стратегії:
1. High Confidence Agreement - обидві моделі згодні з високою впевненістю
2. Disagreement with High Confidence - одна модель дуже впевнена, інша ні
3. Both Uncertain - обидві моделі невпевнені → triage потрібен
4. Contradictory High Confidence - обидві впевнені але не згодні → triage
"""
from typing import Optional, Tuple, Dict
from app.core.enums import PriorityEnum, TriageReasonEnum


class EnsembleService:
    """
    Сервіс для ensemble decision making між ML та LLM моделями.
    """

    # Пороги для decision making
    HIGH_CONFIDENCE_THRESHOLD = 0.75  # >= 75% вважається високою впевненістю
    LOW_CONFIDENCE_THRESHOLD = 0.50   # < 50% вважається низькою впевненістю

    # Ваги для weighted voting
    ML_WEIGHT = 0.55  # ML модель має трохи більшу вагу (навчена на наших даних)
    LLM_WEIGHT = 0.45  # LLM має менше ваги (general purpose)

    @staticmethod
    def combine_predictions(
        ml_priority: Optional[PriorityEnum],
        ml_confidence: Optional[float],
        llm_priority: Optional[PriorityEnum],
        llm_confidence: Optional[float],
    ) -> Tuple[PriorityEnum, float, bool, Optional[TriageReasonEnum], str]:
        """
        Комбінує predictions з ML та LLM моделей.

        Args:
            ml_priority: Priority з ML моделі (P1/P2/P3)
            ml_confidence: Confidence ML моделі (0-1)
            llm_priority: Priority з LLM (P1/P2/P3)
            llm_confidence: Confidence LLM (0-1)

        Returns:
            Tuple[
                final_priority: PriorityEnum,
                final_confidence: float,
                needs_triage: bool,
                triage_reason: Optional[TriageReasonEnum],
                reasoning: str  # Пояснення рішення
            ]
        """

        # === Case 1: Обидві моделі недоступні ===
        if ml_priority is None and llm_priority is None:
            return (
                PriorityEnum.P3,  # Default to low priority
                0.0,
                True,
                TriageReasonEnum.ML_DISABLED,
                "Both ML and LLM unavailable, defaulting to P3 with triage required"
            )

        # === Case 2: Тільки ML доступна ===
        if ml_priority is not None and llm_priority is None:
            needs_triage = ml_confidence < EnsembleService.HIGH_CONFIDENCE_THRESHOLD
            triage_reason = TriageReasonEnum.LOW_PRIORITY_CONF if needs_triage else None
            return (
                ml_priority,
                ml_confidence,
                needs_triage,
                triage_reason,
                f"Only ML available, confidence={ml_confidence:.2f}"
            )

        # === Case 3: Тільки LLM доступна ===
        if ml_priority is None and llm_priority is not None:
            needs_triage = llm_confidence < EnsembleService.HIGH_CONFIDENCE_THRESHOLD
            triage_reason = TriageReasonEnum.LOW_PRIORITY_CONF if needs_triage else None
            return (
                llm_priority,
                llm_confidence,
                needs_triage,
                triage_reason,
                f"Only LLM available, confidence={llm_confidence:.2f}"
            )

        # === Case 4: Обидві моделі доступні ===

        # Strategy 1: HIGH CONFIDENCE AGREEMENT
        if (
            ml_priority == llm_priority
            and ml_confidence >= EnsembleService.HIGH_CONFIDENCE_THRESHOLD
            and llm_confidence >= EnsembleService.HIGH_CONFIDENCE_THRESHOLD
        ):
            # Обидві згодні з високою впевненістю → дуже надійне рішення
            combined_confidence = (ml_confidence + llm_confidence) / 2
            return (
                ml_priority,
                combined_confidence,
                False,  # Triage не потрібен
                None,
                f"High confidence agreement: ML={ml_confidence:.2f}, LLM={llm_confidence:.2f}"
            )

        # Strategy 2: AGREEMENT WITH MODERATE CONFIDENCE
        if ml_priority == llm_priority:
            # Згодні, але принаймні одна має низьку впевненість
            combined_confidence = (ml_confidence + llm_confidence) / 2

            # Якщо середня впевненість достатня → приймаємо
            if combined_confidence >= EnsembleService.LOW_CONFIDENCE_THRESHOLD:
                needs_triage = combined_confidence < EnsembleService.HIGH_CONFIDENCE_THRESHOLD
                triage_reason = TriageReasonEnum.LOW_PRIORITY_CONF if needs_triage else None
                return (
                    ml_priority,
                    combined_confidence,
                    needs_triage,
                    triage_reason,
                    f"Agreement with moderate confidence: avg={combined_confidence:.2f}"
                )
            else:
                # Обидві дуже невпевнені навіть якщо згодні
                return (
                    ml_priority,
                    combined_confidence,
                    True,
                    TriageReasonEnum.LOW_PRIORITY_CONF,
                    f"Agreement but both very uncertain: avg={combined_confidence:.2f}"
                )

        # Strategy 3: DISAGREEMENT - USE HIGHEST CONFIDENCE
        if ml_priority != llm_priority:
            # Різні predictions

            # Якщо одна модель дуже впевнена, а інша ні → довіряємо впевненій
            if (
                ml_confidence >= EnsembleService.HIGH_CONFIDENCE_THRESHOLD
                and llm_confidence < EnsembleService.LOW_CONFIDENCE_THRESHOLD
            ):
                return (
                    ml_priority,
                    ml_confidence,
                    False,
                    None,
                    f"ML highly confident ({ml_confidence:.2f}), LLM uncertain ({llm_confidence:.2f})"
                )

            if (
                llm_confidence >= EnsembleService.HIGH_CONFIDENCE_THRESHOLD
                and ml_confidence < EnsembleService.LOW_CONFIDENCE_THRESHOLD
            ):
                return (
                    llm_priority,
                    llm_confidence,
                    False,
                    None,
                    f"LLM highly confident ({llm_confidence:.2f}), ML uncertain ({ml_confidence:.2f})"
                )

            # Strategy 4: WEIGHTED VOTING
            # Якщо обидві мають помірну впевненість але не згодні
            if (
                ml_confidence >= EnsembleService.LOW_CONFIDENCE_THRESHOLD
                and llm_confidence >= EnsembleService.LOW_CONFIDENCE_THRESHOLD
            ):
                # Використовуємо weighted voting
                ml_score = ml_confidence * EnsembleService.ML_WEIGHT
                llm_score = llm_confidence * EnsembleService.LLM_WEIGHT

                if ml_score > llm_score:
                    final_priority = ml_priority
                    final_confidence = ml_confidence
                    reasoning = f"Weighted voting: ML wins (ML:{ml_score:.2f} vs LLM:{llm_score:.2f})"
                else:
                    final_priority = llm_priority
                    final_confidence = llm_confidence
                    reasoning = f"Weighted voting: LLM wins (LLM:{llm_score:.2f} vs ML:{ml_score:.2f})"

                # Якщо це близький матч → потрібен triage
                needs_triage = abs(ml_score - llm_score) < 0.1
                triage_reason = TriageReasonEnum.LLM_PRIORITY_MISMATCH if needs_triage else None

                return (
                    final_priority,
                    final_confidence,
                    needs_triage,
                    triage_reason,
                    reasoning
                )

            # Strategy 5: HIGH CONFIDENCE DISAGREEMENT (CRITICAL CASE)
            if (
                ml_confidence >= EnsembleService.HIGH_CONFIDENCE_THRESHOLD
                and llm_confidence >= EnsembleService.HIGH_CONFIDENCE_THRESHOLD
            ):
                # Обидві дуже впевнені але не згодні → ОБОВ'ЯЗКОВИЙ triage
                # Вибираємо вищий priority для безпеки (краще escalate ніж miss)
                priority_order = {PriorityEnum.P1: 3, PriorityEnum.P2: 2, PriorityEnum.P3: 1}
                final_priority = (
                    ml_priority
                    if priority_order[ml_priority] > priority_order[llm_priority]
                    else llm_priority
                )

                return (
                    final_priority,
                    (ml_confidence + llm_confidence) / 2,
                    True,  # ОБОВ'ЯЗКОВИЙ triage
                    TriageReasonEnum.LLM_PRIORITY_MISMATCH,
                    f"Critical: Both highly confident but disagree (ML:{ml_priority.value} vs LLM:{llm_priority.value})"
                )

            # Strategy 6: BOTH VERY UNCERTAIN
            # Обидві моделі дуже невпевнені → завжди triage
            # Вибираємо predictions з вищою впевненістю
            if ml_confidence >= llm_confidence:
                final_priority = ml_priority
                final_confidence = ml_confidence
            else:
                final_priority = llm_priority
                final_confidence = llm_confidence

            return (
                final_priority,
                final_confidence,
                True,
                TriageReasonEnum.LOW_PRIORITY_CONF,
                f"Both uncertain: ML={ml_confidence:.2f}, LLM={llm_confidence:.2f}"
            )

        # Fallback (не повинно сюди потрапити, але для безпеки)
        return (
            PriorityEnum.P3,
            0.5,
            True,
            TriageReasonEnum.MANUAL_FLAG,
            "Fallback: Unexpected ensemble state"
        )

    @staticmethod
    def get_strategy_stats(
        ml_priority: Optional[PriorityEnum],
        ml_confidence: Optional[float],
        llm_priority: Optional[PriorityEnum],
        llm_confidence: Optional[float],
    ) -> Dict[str, any]:
        """
        Повертає додаткову статистику про ensemble decision.

        Returns:
            Dict з ключами:
            - strategy_used: назва стратегії
            - agreement: bool - чи згодні моделі
            - ml_confident: bool - чи ML впевнена
            - llm_confident: bool - чи LLM впевнена
            - confidence_gap: різниця між confidences
        """
        if ml_priority is None or llm_priority is None:
            return {
                "strategy_used": "single_model",
                "agreement": None,
                "ml_confident": ml_confidence >= EnsembleService.HIGH_CONFIDENCE_THRESHOLD if ml_confidence else None,
                "llm_confident": llm_confidence >= EnsembleService.HIGH_CONFIDENCE_THRESHOLD if llm_confidence else None,
                "confidence_gap": None
            }

        agreement = ml_priority == llm_priority
        ml_confident = ml_confidence >= EnsembleService.HIGH_CONFIDENCE_THRESHOLD
        llm_confident = llm_confidence >= EnsembleService.HIGH_CONFIDENCE_THRESHOLD
        confidence_gap = abs(ml_confidence - llm_confidence)

        # Визначаємо яка стратегія буде використана
        if agreement and ml_confident and llm_confident:
            strategy = "high_confidence_agreement"
        elif agreement:
            strategy = "moderate_agreement"
        elif ml_confident and not llm_confident:
            strategy = "ml_dominance"
        elif llm_confident and not ml_confident:
            strategy = "llm_dominance"
        elif ml_confident and llm_confident:
            strategy = "critical_disagreement"
        else:
            strategy = "weighted_voting"

        return {
            "strategy_used": strategy,
            "agreement": agreement,
            "ml_confident": ml_confident,
            "llm_confident": llm_confident,
            "confidence_gap": round(confidence_gap, 3)
        }


# Глобальний інстанс
ensemble_service = EnsembleService()
