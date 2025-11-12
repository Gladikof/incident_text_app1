"""
Tickets Router - API endpoints для роботи з тікетами.
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.core.deps import (
    get_current_active_user,
    require_lead_or_admin,
    require_agent_or_higher,
)
from app.core.enums import StatusEnum, PriorityEnum, CategoryEnum, RoleEnum
from app.models.user import User
from app.models.ticket import Ticket
from app.schemas.ticket import (
    TicketOut,
    TicketCreate,
    TicketUpdate,
    TicketListItem,
    TicketStatusUpdate,
    TicketAssign,
    TicketTriageResolve,
)
from app.services.ticket_service import ticket_service
from app.services.ml_service import ml_service


router = APIRouter(prefix="/tickets", tags=["tickets"])


@router.post("", response_model=TicketOut, status_code=201)
def create_ticket(
    ticket_data: TicketCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """
    Створити новий тікет з ML-класифікацією.

    Доступно: всім авторизованим користувачам.

    Бізнес-логіка:
    1. Створюється тікет
    2. Викликається ML-пайплайн
    3. Порівнюється впевненість з порогами
    4. Визначається статус (NEW або TRIAGE)
    5. Застосовується AUTO_APPLY режим (якщо ввімкнено)
    """
    ticket = ticket_service.create_ticket(
        ticket_data=ticket_data,
        creator=current_user,
        db=db,
    )
    return ticket


@router.get("", response_model=List[TicketListItem])
def list_tickets(
    status: Optional[StatusEnum] = Query(None, description="Фільтр за статусом"),
    priority: Optional[PriorityEnum] = Query(None, description="Фільтр за пріоритетом"),
    category: Optional[CategoryEnum] = Query(None, description="Фільтр за категорією"),
    department_id: Optional[int] = Query(None, description="Фільтр за департаментом"),
    assignee_id: Optional[int] = Query(None, description="Фільтр за виконавцем"),
    creator_id: Optional[int] = Query(None, description="Фільтр за автором"),
    triage_required: Optional[bool] = Query(None, description="Тільки тікети на тріажі"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """
    Список тікетів з фільтрами.

    Доступно: всім авторизованим користувачам.

    Permissions:
    - USER: бачить тільки свої тікети
    - AGENT: бачить тікети свого департаменту + призначені йому
    - LEAD: бачить тікети свого департаменту
    - ADMIN: бачить всі тікети
    """
    query = db.query(Ticket)

    # Permissions
    if current_user.role == RoleEnum.USER:
        # USER бачить тільки свої тікети
        query = query.filter(Ticket.created_by_user_id == current_user.id)
    elif current_user.role == RoleEnum.AGENT:
        # AGENT бачить тікети свого департаменту або призначені йому
        query = query.filter(
            (Ticket.department_id == current_user.department_id) |
            (Ticket.assigned_to_user_id == current_user.id)
        )
    elif current_user.role == RoleEnum.LEAD:
        # LEAD бачить тікети свого департаменту
        if current_user.department_id:
            query = query.filter(Ticket.department_id == current_user.department_id)
    # ADMIN бачить всі тікети (без фільтра)

    # Фільтри
    if status:
        query = query.filter(Ticket.status == status)
    if priority:
        query = query.filter(Ticket.priority_manual == priority)
    if category:
        query = query.filter(Ticket.category == category)
    if department_id:
        query = query.filter(Ticket.department_id == department_id)
    if assignee_id:
        query = query.filter(Ticket.assigned_to_user_id == assignee_id)
    if creator_id:
        query = query.filter(Ticket.created_by_user_id == creator_id)
    if triage_required is not None:
        query = query.filter(Ticket.triage_required == triage_required)

    # Сортування: спочатку нові та на тріажі
    query = query.order_by(
        Ticket.triage_required.desc(),
        Ticket.created_at.desc(),
    )

    tickets = query.all()
    return tickets


@router.get("/{ticket_id}", response_model=TicketOut)
def get_ticket(
    ticket_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """
    Отримати деталі тікета.

    Доступно: всім авторизованим користувачам (з перевіркою прав).
    """
    ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")

    # Permissions
    if current_user.role == RoleEnum.USER:
        if ticket.created_by_user_id != current_user.id:
            raise HTTPException(status_code=403, detail="Access denied")
    elif current_user.role in [RoleEnum.AGENT, RoleEnum.LEAD]:
        if ticket.department_id != current_user.department_id and ticket.assigned_to_user_id != current_user.id:
            raise HTTPException(status_code=403, detail="Access denied")
    # ADMIN має доступ до всіх тікетів

    return ticket


@router.patch("/{ticket_id}", response_model=TicketOut)
def update_ticket(
    ticket_id: int,
    ticket_data: TicketUpdate,
    current_user: User = Depends(require_agent_or_higher),
    db: Session = Depends(get_db),
):
    """
    Оновити тікет.

    Доступно: AGENT, LEAD, ADMIN.
    """
    ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")

    # Permissions: AGENT може редагувати тільки призначені йому тікети
    if current_user.role == RoleEnum.AGENT:
        if ticket.assigned_to_user_id != current_user.id:
            raise HTTPException(status_code=403, detail="Access denied")

    updated_ticket = ticket_service.update_ticket(
        ticket_id=ticket_id,
        ticket_data=ticket_data,
        db=db,
    )
    return updated_ticket


@router.patch("/{ticket_id}/status", response_model=TicketOut)
def update_ticket_status(
    ticket_id: int,
    status_data: TicketStatusUpdate,
    current_user: User = Depends(require_agent_or_higher),
    db: Session = Depends(get_db),
):
    """
    Оновити статус тікета.

    Доступно: AGENT (тільки свої тікети), LEAD, ADMIN.
    """
    ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")

    # Permissions
    if current_user.role == RoleEnum.AGENT:
        if ticket.assigned_to_user_id != current_user.id:
            raise HTTPException(status_code=403, detail="Access denied")

    updated_ticket = ticket_service.update_status(
        ticket_id=ticket_id,
        new_status=status_data.status,
        db=db,
    )
    return updated_ticket


@router.post("/{ticket_id}/claim", response_model=TicketOut)
def claim_ticket(
    ticket_id: int,
    current_user: User = Depends(require_agent_or_higher),
    db: Session = Depends(get_db),
):
    """
    AGENT забирає тікет собі (self-assign).

    Доступно: AGENT, LEAD.

    Обмеження:
    - Тікет не на тріажі (self_assign_locked=False)
    - Тікет ще не призначений
    - Scope (DEPT або ALL) згідно з SystemSettings
    """
    if current_user.role not in [RoleEnum.AGENT, RoleEnum.LEAD]:
        raise HTTPException(status_code=403, detail="Only agents can claim tickets")

    ticket = ticket_service.claim_ticket(
        ticket_id=ticket_id,
        agent=current_user,
        db=db,
    )
    return ticket


@router.patch("/{ticket_id}/assign", response_model=TicketOut)
def assign_ticket(
    ticket_id: int,
    assign_data: TicketAssign,
    current_user: User = Depends(require_lead_or_admin),
    db: Session = Depends(get_db),
):
    """
    LEAD/ADMIN призначає тікет конкретному AGENT.

    Доступно: LEAD, ADMIN.
    """
    ticket = ticket_service.assign_ticket(
        ticket_id=ticket_id,
        assignee_id=assign_data.assigned_to_user_id,
        db=db,
    )
    return ticket


@router.patch("/{ticket_id}/triage/resolve", response_model=TicketOut)
def resolve_triage(
    ticket_id: int,
    triage_data: TicketTriageResolve,
    current_user: User = Depends(require_lead_or_admin),
    db: Session = Depends(get_db),
):
    """
    LEAD вирішує тріаж: підтверджує або змінює ML рекомендації.

    Доступно: LEAD, ADMIN.

    Після вирішення тріажу:
    - triage_required=False
    - self_assign_locked=False
    - status=NEW (готовий до взяття AGENT)
    """
    ticket = ticket_service.resolve_triage(
        ticket_id=ticket_id,
        priority_final=triage_data.priority_final,
        category_final=triage_data.category_final,
        lead=current_user,
        db=db,
    )
    return ticket


@router.post("/{ticket_id}/ml/recalculate", response_model=TicketOut)
def recalculate_ml(
    ticket_id: int,
    current_user: User = Depends(require_lead_or_admin),
    db: Session = Depends(get_db),
):
    """
    Перезапустити ML-класифікацію для тікета.

    Доступно: LEAD, ADMIN.

    Використовується, якщо:
    - Оновилася ML модель
    - Змінився опис тікета
    - Потрібна повторна оцінка
    """
    ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")

    # Викликаємо ML заново
    ml_result = ml_service.predict_ticket(
        title=ticket.title,
        description=ticket.description,
        db=db,
        ticket_id=ticket.id,
    )

    # Оновлюємо ML поля
    ticket.priority_ml_suggested = ml_result["priority_ml_suggested"]
    ticket.priority_ml_confidence = ml_result["priority_ml_confidence"]
    ticket.category_ml_suggested = ml_result["category_ml_suggested"]
    ticket.category_ml_confidence = ml_result["category_ml_confidence"]
    ticket.ml_model_version = ml_result["ml_model_version"]
    ticket.triage_required = ml_result["triage_required"]
    ticket.triage_reason = ml_result["triage_reason"]

    db.commit()
    db.refresh(ticket)

    return ticket


@router.post("/{ticket_id}/assignment/confirm")
def confirm_assignment(
    ticket_id: int,
    confirmed: bool,
    feedback: Optional[str] = None,
    current_user: User = Depends(require_agent_or_higher),
    db: Session = Depends(get_db),
):
    """
    Підтвердити або відхилити автоматичне призначення тікету.

    Доступно: AGENT, LEAD, ADMIN (тільки той, кому призначено тікет).

    Args:
        ticket_id: ID тікету
        confirmed: True = підтверджую, False = відхиляю (не мій відділ/спеціалізація)
        feedback: Опціональний коментар від спеціаліста

    Використання для навчання:
    - confirmed=True → позитивна класифікація (система правильно призначила)
    - confirmed=False → негативна класифікація (система помилилась, треба перенавчити)
    """
    from datetime import datetime

    ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")

    # Перевіряємо що тікет призначено поточному користувачу
    if ticket.assigned_to_user_id != current_user.id:
        raise HTTPException(
            status_code=403,
            detail="You can only confirm/reject assignments for tickets assigned to you"
        )

    # Перевіряємо що це автоматичне призначення
    if not ticket.auto_assigned:
        raise HTTPException(
            status_code=400,
            detail="This ticket was not auto-assigned"
        )

    # Перевіряємо що ще не підтверджено
    if ticket.assignment_confirmed is not None:
        raise HTTPException(
            status_code=400,
            detail="Assignment already confirmed/rejected"
        )

    # Зберігаємо підтвердження
    ticket.assignment_confirmed = confirmed
    ticket.assignment_confirmed_at = datetime.utcnow()
    ticket.assignment_feedback = feedback

    # Якщо відхилено - знімаємо призначення
    if not confirmed:
        ticket.assigned_to_user_id = None
        ticket.status = StatusEnum.TRIAGE  # Відправляємо в тріаж для ручного призначення
        print(f"[ASSIGNMENT REJECTED] Тікет #{ticket.incident_id} відхилено {current_user.full_name}. Причина: {feedback}")
    else:
        print(f"[ASSIGNMENT CONFIRMED] Тікет #{ticket.incident_id} підтверджено {current_user.full_name}")

    db.commit()
    db.refresh(ticket)

    return {
        "success": True,
        "ticket_id": ticket.id,
        "confirmed": confirmed,
        "message": "Дякуємо за підтвердження!" if confirmed else "Тікет буде перепризначено через LEAD"
    }
