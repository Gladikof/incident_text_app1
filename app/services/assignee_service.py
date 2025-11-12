"""
Сервіс для автоматичного призначення спеціаліста на основі:
1. Категорії тікета (ML prediction)
2. Завантаженості спеціаліста (кількість активних тікетів)
3. Досвіду з категорією (кількість вирішених тікетів по категорії)
4. Збігу ключових слів тікета з профілем експертизи спеціаліста (learning-based)
"""
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import func, case

from app.models import User, Ticket
from app.core.enums import RoleEnum, StatusEnum, CategoryEnum


class AssigneeService:
    """Сервіс для рекомендації виконавця"""

    @staticmethod
    def recommend_assignee(
        category: Optional[CategoryEnum],
        department_id: Optional[int],
        db: Session
    ) -> Optional[User]:
        """
        Рекомендує спеціаліста на основі категорії тікета.

        Логіка:
        1. Знаходить всіх AGENT з потрібного департаменту
        2. Рахує активні тікети (NEW, TRIAGE, IN_PROGRESS)
        3. Рахує досвід по категорії (RESOLVED, CLOSED тікети з цією категорією)
        4. Вибирає спеціаліста з найменшою завантаженістю і найбільшим досвідом

        Args:
            category: Категорія тікета (Hardware/Software/Network/Access/Other)
            department_id: ID департаменту
            db: DB сесія

        Returns:
            User або None
        """
        if not category or not department_id:
            return None

        # 1. Знаходимо всіх агентів з департаменту
        agents = db.query(User).filter(
            User.role == RoleEnum.AGENT,
            User.department_id == department_id,
            User.is_active == True
        ).all()

        if not agents:
            return None

        # 2. Для кожного агента рахуємо метрики
        agent_scores = []
        for agent in agents:
            # Кількість активних тікетів
            active_count = db.query(Ticket).filter(
                Ticket.agent_id == agent.id,
                Ticket.status.in_([StatusEnum.NEW, StatusEnum.TRIAGE, StatusEnum.IN_PROGRESS])
            ).count()

            # Кількість вирішених тікетів по категорії
            experience_count = db.query(Ticket).filter(
                Ticket.agent_id == agent.id,
                Ticket.status.in_([StatusEnum.RESOLVED, StatusEnum.CLOSED]),
                Ticket.category_final == category
            ).count()

            # Альтернатива: рахуємо по ML suggested category якщо category_final не встановлено
            if experience_count == 0:
                experience_count = db.query(Ticket).filter(
                    Ticket.agent_id == agent.id,
                    Ticket.status.in_([StatusEnum.RESOLVED, StatusEnum.CLOSED]),
                    Ticket.category_ml_suggested == category
                ).count()

            # Скор: мінус активні (менше = краще) + досвід (більше = краще)
            # Вага: досвід важливіший, тому множимо на 2
            score = (experience_count * 2) - active_count

            agent_scores.append({
                'agent': agent,
                'score': score,
                'active_count': active_count,
                'experience_count': experience_count
            })

        # 3. Сортуємо за скором (більший = кращий)
        agent_scores.sort(key=lambda x: x['score'], reverse=True)

        # 4. Повертаємо найкращого
        best = agent_scores[0]
        print(f"[ASSIGNEE] Обрано: {best['agent'].full_name} "
              f"(активних: {best['active_count']}, досвід з {category.value}: {best['experience_count']}, "
              f"score: {best['score']})")

        return best['agent']

    @staticmethod
    def recommend_by_name_pattern(
        category: Optional[CategoryEnum],
        department_id: Optional[int],
        db: Session
    ) -> Optional[User]:
        """
        Альтернативна логіка: призначає спеціаліста за іменем.
        Наприклад, john.hardware -> Hardware, bob.software -> Software

        Це для демо-цілей, показує що є різні стратегії.
        """
        if not category or not department_id:
            return None

        # Мапінг категорії на частину email
        category_keywords = {
            CategoryEnum.HARDWARE: "hardware",
            CategoryEnum.SOFTWARE: "software",
            CategoryEnum.NETWORK: "network",
            CategoryEnum.ACCESS: "access",
            CategoryEnum.OTHER: None  # для Other беремо будь-кого
        }

        keyword = category_keywords.get(category)

        # Знаходимо агентів з потрібним keyword в email
        agents = db.query(User).filter(
            User.role == RoleEnum.AGENT,
            User.department_id == department_id,
            User.is_active == True
        )

        if keyword:
            agents = agents.filter(User.email.contains(keyword))

        agents_list = agents.all()

        if not agents_list:
            # Якщо немає спеціалізованого, беремо будь-якого з департаменту
            agents_list = db.query(User).filter(
                User.role == RoleEnum.AGENT,
                User.department_id == department_id,
                User.is_active == True
            ).all()

        if not agents_list:
            return None

        # З відфільтрованих беремо найменш завантаженого
        best_agent = None
        min_active = float('inf')

        for agent in agents_list:
            active_count = db.query(Ticket).filter(
                Ticket.agent_id == agent.id,
                Ticket.status.in_([StatusEnum.NEW, StatusEnum.TRIAGE, StatusEnum.IN_PROGRESS])
            ).count()

            if active_count < min_active:
                min_active = active_count
                best_agent = agent

        if best_agent:
            print(f"[ASSIGNEE BY NAME] Обрано: {best_agent.full_name} (активних: {min_active})")

        return best_agent

    @staticmethod
    def recommend_by_expertise(
        ticket_text: str,
        category: Optional[CategoryEnum],
        department_id: Optional[int],
        db: Session
    ) -> Optional[User]:
        """
        Рекомендує спеціаліста на основі збігу ключових слів тікета
        з профілем експертизи (навчається на історичних даних).

        Використовує LearningService для аналізу вирішених тікетів та підбору
        найбільш досвідченого спеціаліста для конкретного типу проблеми.

        Args:
            ticket_text: Повний текст тікета (title + description)
            category: ML-передбачена категорія
            department_id: ID департаменту
            db: DB сесія

        Returns:
            User або None
        """
        from app.services.learning_service import learning_service

        recommended_agent = learning_service.match_ticket_to_specialist_by_expertise(
            ticket_text=ticket_text,
            category=category,
            department_id=department_id,
            db=db
        )

        if recommended_agent:
            print(f"[ASSIGNEE BY EXPERTISE] Обрано: {recommended_agent.full_name} "
                  f"(на основі аналізу ключових слів та історії вирішених тікетів)")

        return recommended_agent


assignee_service = AssigneeService()
