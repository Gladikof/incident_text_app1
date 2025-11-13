"""
Ticket Service - бізнес-логіка роботи з тікетами.
Містить логіку створення, оновлення, тріажу та статусів.
"""
from typing import Optional, List
from datetime import datetime

from sqlalchemy.orm import Session
from fastapi import HTTPException

from app.core.enums import (
    StatusEnum, PriorityEnum, RoleEnum, MLModeEnum,
    TriageReasonEnum, CategoryEnum
)
from app.models.ticket import Ticket
from app.models.user import User
from app.models.settings import SystemSettings
from app.schemas.ticket import TicketCreate, TicketUpdate
from app.services.ml_service import ml_service
from app.services.assignee_service import assignee_service


class TicketService:
    """
    Сервіс для управління тікетами.
    """

    @staticmethod
    def create_ticket(
        ticket_data: TicketCreate,
        creator: User,
        db: Session,
    ) -> Ticket:
        """
        Створення тікета з ML-класифікацією та логікою тріажу.

        Бізнес-логіка згідно з §4 вимог:
        1. Створити запис тікета
        2. Викликати ML-пайплайн
        3. Порівняти впевненість з порогами
        4. Визначити чи потрібен тріаж
        5. Застосувати AUTO_APPLY або RECOMMEND режим
        6. Встановити статус (NEW або TRIAGE)

        Args:
            ticket_data: Дані для створення тікета
            creator: Користувач, що створює тікет
            db: Database session

        Returns:
            Створений Ticket
        """
        settings = TicketService._get_settings(db)

        # 1. Створити базовий тікет
        ticket = Ticket(
            title=ticket_data.title,
            description=ticket_data.description,
            created_by_user_id=creator.id,
            department_id=ticket_data.department_id,
            asset_id=ticket_data.asset_id,
            priority_manual=ticket_data.priority_manual or PriorityEnum.P3,
            status=StatusEnum.NEW,
            triage_required=False,
        )

        db.add(ticket)
        db.flush()  # Отримуємо ID без commit (incident_id буде згенеровано автоматично)

        # 2. ML класифікація (якщо ввімкнено)
        if settings.feature_ml_enabled:
            ml_result = ml_service.predict_ticket(
                title=ticket.title,
                description=ticket.description,
                db=db,
                ticket_id=ticket.id,
            )

            # Заповнюємо ML поля
            ticket.priority_ml_suggested = ml_result["priority_ml_suggested"]
            ticket.priority_ml_confidence = ml_result["priority_ml_confidence"]
            ticket.category_ml_suggested = ml_result["category_ml_suggested"]
            ticket.category_ml_confidence = ml_result["category_ml_confidence"]
            ticket.ml_model_version = ml_result["ml_model_version"]
            ticket.triage_required = ml_result["triage_required"]
            ticket.triage_reason = ml_result["triage_reason"]

            # 3. Логіка AUTO_APPLY режиму
            if settings.ml_mode == MLModeEnum.AUTO_APPLY and not ticket.triage_required:
                # Автоматично застосовуємо ML рекомендації
                if ticket.priority_ml_suggested:
                    ticket.priority_manual = ticket.priority_ml_suggested
                    ticket.priority_accepted = True

                if ticket.category_ml_suggested:
                    ticket.category = ticket.category_ml_suggested
                    ticket.category_accepted = True

            # 3.5. Автоматичне призначення спеціаліста (якщо високий confidence)
            if not ticket.triage_required and ticket.category_ml_suggested:
                # Спочатку пробуємо learning-based метод (на основі ключових слів та історії)
                full_text = f"{ticket.title}\n{ticket.description}"
                recommended_agent = assignee_service.recommend_by_expertise(
                    ticket_text=full_text,
                    category=ticket.category_ml_suggested,
                    department_id=ticket.department_id,
                    db=db
                )

                # Якщо learning-based метод не знайшов (немає історії), fallback на recommend_assignee
                if not recommended_agent:
                    recommended_agent = assignee_service.recommend_assignee(
                        category=ticket.category_ml_suggested,
                        department_id=ticket.department_id,
                        db=db
                    )

                if recommended_agent:
                    ticket.assigned_to_user_id = recommended_agent.id
                    ticket.auto_assigned = True  # Позначаємо що призначено автоматично
                    ticket.assignment_confirmed = None  # Очікує підтвердження від спеціаліста
                    print(f"[AUTO-ASSIGN] Тікет #{ticket.incident_id} призначено {recommended_agent.full_name}")

            # 4. Визначення статусу
            if ticket.triage_required:
                ticket.status = StatusEnum.TRIAGE
                ticket.self_assign_locked = True  # Блокуємо self-assign до тріажу

                # Автоматично призначити на LEAD департаменту
                if ticket.department_id:
                    from app.models.department import Department
                    dept = db.query(Department).filter(Department.id == ticket.department_id).first()
                    if dept and dept.lead_user_id:
                        ticket.assigned_to_user_id = dept.lead_user_id
                        ticket.auto_assigned = False  # Це системне призначення, не ML
                        print(f"[TRIAGE AUTO-ASSIGN] Тікет #{ticket.incident_id} призначено на LEAD департаменту (user_id: {dept.lead_user_id})")
            else:
                ticket.status = StatusEnum.NEW

        else:
            # ML вимкнено - відразу тріаж
            ticket.triage_required = True
            ticket.triage_reason = TriageReasonEnum.ML_DISABLED
            ticket.status = StatusEnum.TRIAGE
            ticket.self_assign_locked = True

            # Автоматично призначити на LEAD департаменту
            if ticket.department_id:
                from app.models.department import Department
                dept = db.query(Department).filter(Department.id == ticket.department_id).first()
                if dept and dept.lead_user_id:
                    ticket.assigned_to_user_id = dept.lead_user_id
                    ticket.auto_assigned = False
                    print(f"[TRIAGE AUTO-ASSIGN] Тікет #{ticket.incident_id} призначено на LEAD департаменту (user_id: {dept.lead_user_id})")

        db.commit()
        db.refresh(ticket)

        return ticket

    @staticmethod
    def update_ticket(
        ticket_id: int,
        ticket_data: TicketUpdate,
        actor: User,
        db: Session,
    ) -> Ticket:
        """
        Оновлення тікета.

        Args:
            ticket_id: ID тікета
            ticket_data: Нові дані
            db: Database session

        Returns:
            Оновлений Ticket
        """
        ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
        if not ticket:
            raise HTTPException(status_code=404, detail="Ticket not found")

        # Оновлюємо тільки передані поля
        update_data = ticket_data.dict(exclude_unset=True)

        priority_reason = update_data.pop("priority_manual_reason", None)
        new_priority = update_data.get("priority_manual")
        priority_changed = False
        previous_priority = ticket.priority_manual

        if "priority_manual" in update_data:
            if new_priority is None:
                raise HTTPException(status_code=422, detail="priority_manual cannot be null")
            if new_priority != ticket.priority_manual:
                priority_changed = True
                if not priority_reason or not priority_reason.strip():
                    raise HTTPException(
                        status_code=422,
                        detail="Please provide a reason when overriding the priority",
                    )

        for field, value in update_data.items():
            setattr(ticket, field, value)

        ticket.updated_at = datetime.utcnow()

        if priority_changed:
            TicketService._record_priority_feedback(
                db=db,
                ticket=ticket,
                actor=actor,
                previous_priority=previous_priority,
                new_priority=new_priority,
                reason=priority_reason,
            )

        db.commit()

        if priority_changed:
            try:
                training_feedback_service.export_priority_feedback_dataset(db)
            except Exception as exc:
                print(f"[TRAINING_FEEDBACK] Failed to export dataset: {exc}")

        db.refresh(ticket)

        return ticket

    @staticmethod
    def resolve_triage(
        ticket_id: int,
        priority_final: PriorityEnum,
        category_final: CategoryEnum,
        lead: User,
        db: Session,
        priority_change_reason: Optional[str] = None,
    ) -> Ticket:
        """
        LEAD вирішує тріаж: підтверджує або змінює ML рекомендації.

        Args:
            ticket_id: ID тікета
            priority_final: Фінальний пріоритет
            category_final: Фінальна категорія
            lead: LEAD користувач
            db: Database session

        Returns:
            Оновлений Ticket
        """
        ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
        if not ticket:
            raise HTTPException(status_code=404, detail="Ticket not found")

        if not ticket.triage_required:
            raise HTTPException(status_code=400, detail="Ticket does not require triage")

        previous_priority = ticket.priority_manual

        # Застосовуємо рішення LEAD
        ticket.priority_manual = priority_final
        ticket.category = category_final
        ticket.priority_accepted = True
        ticket.category_accepted = True

        # Знімаємо тріаж
        ticket.triage_required = False
        ticket.triage_reason = None
        ticket.self_assign_locked = False
        ticket.status = StatusEnum.NEW

        ticket.updated_at = datetime.utcnow()

        if priority_final == previous_priority:
            reason_to_store = priority_change_reason or "TRIAGE_CONFIRMED"
        else:
            if not priority_change_reason or not priority_change_reason.strip():
                raise HTTPException(
                    status_code=422,
                    detail="Please explain why the priority differs from the previous value",
                )
            reason_to_store = priority_change_reason

        TicketService._record_priority_feedback(
            db=db,
            ticket=ticket,
            actor=lead,
            previous_priority=previous_priority,
            new_priority=priority_final,
            reason=reason_to_store,
        )

        db.commit()
        try:
            training_feedback_service.export_priority_feedback_dataset(db)
        except Exception as exc:
            print(f"[TRAINING_FEEDBACK] Failed to export dataset: {exc}")
        db.refresh(ticket)

        return ticket

    @staticmethod
    def _record_priority_feedback(
        db: Session,
        ticket: Ticket,
        actor: User,
        previous_priority: Optional[PriorityEnum],
        new_priority: PriorityEnum,
        reason: Optional[str],
    ) -> None:
        log_entry = (
            db.query(MLPredictionLog)
            .filter(MLPredictionLog.ticket_id == ticket.id)
            .order_by(MLPredictionLog.created_at.desc())
            .first()
        )

        if not log_entry:
            log_entry = MLPredictionLog(
                ticket_id=ticket.id,
                model_version=ticket.ml_model_version or "unknown",
                priority_predicted=ticket.priority_ml_suggested,
                priority_confidence=ticket.priority_ml_confidence,
                category_predicted=ticket.category_ml_suggested,
                category_confidence=ticket.category_ml_confidence,
                triage_reason=ticket.triage_reason,
            )
            db.add(log_entry)

        log_entry.priority_final = new_priority
        log_entry.category_final = ticket.category
        log_entry.priority_feedback_previous = previous_priority
        log_entry.priority_feedback_reason = reason
        log_entry.priority_feedback_author_id = actor.id if actor else None
        log_entry.priority_feedback_recorded_at = datetime.utcnow()

        if ticket.priority_ml_suggested and not log_entry.priority_predicted:
            log_entry.priority_predicted = ticket.priority_ml_suggested
            log_entry.priority_confidence = ticket.priority_ml_confidence
        if ticket.category_ml_suggested and not log_entry.category_predicted:
            log_entry.category_predicted = ticket.category_ml_suggested
            log_entry.category_confidence = ticket.category_ml_confidence

        db.flush()

    @staticmethod
    def claim_ticket(
        ticket_id: int,
        agent: User,
        db: Session,
    ) -> Ticket:
        """
        AGENT забирає тікет собі (self-assign).

        Args:
            ticket_id: ID тікета
            agent: AGENT користувач
            db: Database session

        Returns:
            Оновлений Ticket
        """
        settings = TicketService._get_settings(db)

        if not settings.agents_can_self_assign:
            raise HTTPException(status_code=403, detail="Self-assign is disabled")

        ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
        if not ticket:
            raise HTTPException(status_code=404, detail="Ticket not found")

        # LEAD може взяти будь-який тікет, навіть на тріажі
        if ticket.self_assign_locked and agent.role != RoleEnum.LEAD:
            raise HTTPException(
                status_code=403,
                detail="Ticket is locked for self-assign (pending triage)",
            )

        if ticket.assigned_to_user_id:
            raise HTTPException(status_code=400, detail="Ticket already assigned")

        # Перевірка scope (DEPT vs ALL)
        if hasattr(settings, 'agent_visibility_scope') and settings.agent_visibility_scope:
            if settings.agent_visibility_scope.name == "DEPT":
                if agent.department_id != ticket.department_id:
                    raise HTTPException(
                        status_code=403,
                        detail="Can only claim tickets from your department",
                    )

        ticket.assigned_to_user_id = agent.id
        ticket.status = StatusEnum.IN_PROGRESS
        ticket.updated_at = datetime.utcnow()

        db.commit()
        db.refresh(ticket)

        return ticket

    @staticmethod
    def assign_ticket(
        ticket_id: int,
        assignee_id: int,
        db: Session,
    ) -> Ticket:
        """
        LEAD/ADMIN присвоює тікет конкретному AGENT.

        Args:
            ticket_id: ID тікета
            assignee_id: ID виконавця
            db: Database session

        Returns:
            Оновлений Ticket
        """
        ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
        if not ticket:
            raise HTTPException(status_code=404, detail="Ticket not found")

        assignee = db.query(User).filter(User.id == assignee_id).first()
        if not assignee or assignee.role not in [RoleEnum.AGENT, RoleEnum.LEAD]:
            raise HTTPException(status_code=400, detail="Invalid assignee")

        ticket.assigned_to_user_id = assignee_id
        if ticket.status == StatusEnum.NEW:
            ticket.status = StatusEnum.IN_PROGRESS
        ticket.updated_at = datetime.utcnow()

        db.commit()
        db.refresh(ticket)

        return ticket

    @staticmethod
    def update_status(
        ticket_id: int,
        new_status: StatusEnum,
        db: Session,
    ) -> Ticket:
        """
        Оновлення статусу тікета.

        Args:
            ticket_id: ID тікета
            new_status: Новий статус
            db: Database session

        Returns:
            Оновлений Ticket
        """
        ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
        if not ticket:
            raise HTTPException(status_code=404, detail="Ticket not found")

        # Валідація переходів статусів (опціонально)
        # Наприклад: NEW -> IN_PROGRESS -> RESOLVED -> CLOSED
        # TRIAGE -> NEW (після вирішення тріажу)

        ticket.status = new_status
        ticket.updated_at = datetime.utcnow()

        if new_status == StatusEnum.RESOLVED:
            ticket.resolved_at = datetime.utcnow()
        elif new_status == StatusEnum.CLOSED:
            ticket.closed_at = datetime.utcnow()

        db.commit()
        db.refresh(ticket)

        return ticket

    @staticmethod
    def _get_settings(db: Session) -> SystemSettings:
        """Отримує системні налаштування (singleton)."""
        settings = db.query(SystemSettings).filter(SystemSettings.id == 1).first()
        if not settings:
            settings = SystemSettings(id=1)
            db.add(settings)
            db.commit()
            db.refresh(settings)
        return settings


ticket_service = TicketService()
