"""
Сервіс навчання системи на основі історичних даних
Аналізує вирішені тікети та будує профілі експертизи спеціалістів
"""
from typing import Dict, List, Tuple, Optional
from sqlalchemy.orm import Session
from collections import defaultdict
import re

from app.models import Ticket, User
from app.core.enums import StatusEnum, CategoryEnum, RoleEnum


class LearningService:
    """
    Сервіс для автоматичного навчання на основі історичних даних тікетів.
    Будує профілі експертизи спеціалістів на основі:
    - Кількості вирішених тікетів
    - Ключових слів з описів тікетів
    - Категорій тікетів
    """

    @staticmethod
    def extract_keywords(text: str) -> List[str]:
        """
        Витягує ключові слова з тексту (назва + опис тікету).
        Нормалізує до нижнього регістру та видаляє стоп-слова.
        """
        if not text:
            return []

        # Нормалізуємо до lowercase
        text = text.lower()

        # Простий токенізатор: розділяємо по словах
        words = re.findall(r'\b\w+\b', text)

        # Стоп-слова (українською та англійською)
        stop_words = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
            'of', 'with', 'by', 'from', 'as', 'is', 'was', 'are', 'were', 'been',
            'be', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would',
            'should', 'could', 'may', 'might', 'can', 'this', 'that', 'these', 'those',
            'i', 'you', 'he', 'she', 'it', 'we', 'they', 'my', 'your', 'his', 'her',
            'its', 'our', 'their', 'me', 'him', 'us', 'them',
            'і', 'в', 'на', 'з', 'до', 'за', 'про', 'як', 'не', 'що', 'це', 'той',
            'та', 'або', 'але', 'я', 'ти', 'він', 'вона', 'воно', 'ми', 'ви', 'вони',
            'мій', 'твій', 'його', 'її', 'наш', 'ваш', 'їх', 'мене', 'тебе', 'нас', 'вас', 'їх'
        }

        # Фільтруємо стоп-слова та короткі слова
        keywords = [w for w in words if len(w) > 2 and w not in stop_words]

        return keywords

    @staticmethod
    def build_expertise_profiles(db: Session) -> Dict[int, Dict[str, int]]:
        """
        Будує профілі експертизи для всіх спеціалістів на основі вирішених тікетів.

        Returns:
            Dict[agent_id, Dict[keyword, count]]
            Приклад:
            {
                10: {"vpn": 15, "cisco": 12, "anyconnect": 10, ...},
                11: {"switch": 20, "vlan": 18, "router": 15, ...},
            }
        """
        # Отримуємо всі вирішені/закриті тікети
        # Враховуємо тільки ті, що:
        # 1. Вирішені/закриті
        # 2. Призначені комусь
        # 3. Якщо це auto_assigned - то тільки з assignment_confirmed=True (підтверджені спеціалістом)
        resolved_tickets = db.query(Ticket).filter(
            Ticket.status.in_([StatusEnum.RESOLVED, StatusEnum.CLOSED]),
            Ticket.assigned_to_user_id.isnot(None)
        ).all()

        # Фільтруємо: якщо auto_assigned=True, беремо тільки підтверджені (assignment_confirmed=True)
        # або ті, що не були auto_assigned (ручне призначення завжди вважається правильним)
        valid_tickets = []
        for ticket in resolved_tickets:
            if ticket.auto_assigned:
                # Якщо автоматично призначено - беремо тільки підтверджені
                if ticket.assignment_confirmed is True:
                    valid_tickets.append(ticket)
                # Якщо відхилено (False) або не підтверджено (None) - пропускаємо
            else:
                # Ручне призначення завжди правильне
                valid_tickets.append(ticket)

        resolved_tickets = valid_tickets

        # Словник: agent_id -> {keyword: count}
        expertise: Dict[int, Dict[str, int]] = defaultdict(lambda: defaultdict(int))

        for ticket in resolved_tickets:
            agent_id = ticket.assigned_to_user_id
            if not agent_id:
                continue

            # Об'єднуємо назву та опис
            full_text = f"{ticket.title or ''}\n{ticket.description or ''}"
            keywords = LearningService.extract_keywords(full_text)

            # Збільшуємо лічильник для кожного ключового слова
            for kw in keywords:
                expertise[agent_id][kw] += 1

        return dict(expertise)

    @staticmethod
    def match_ticket_to_specialist_by_expertise(
        ticket_text: str,
        category: Optional[CategoryEnum],
        department_id: Optional[int],
        db: Session
    ) -> Optional[User]:
        """
        Підбирає спеціаліста на основі збігу ключових слів тікету з профілем експертизи.

        Args:
            ticket_text: Текст тікету (title + description)
            category: ML-передбачена категорія
            department_id: ID департаменту
            db: Database session

        Returns:
            User або None якщо не знайдено відповідного спеціаліста
        """
        # 1. Витягуємо ключові слова з тікету
        ticket_keywords = LearningService.extract_keywords(ticket_text)
        if not ticket_keywords:
            return None

        # 2. Отримуємо всіх агентів департаменту
        agents = db.query(User).filter(
            User.role == RoleEnum.AGENT,
            User.department_id == department_id,
            User.is_active == True
        ).all()

        if not agents:
            return None

        # 3. Будуємо профілі експертизи
        expertise_profiles = LearningService.build_expertise_profiles(db)

        # 4. Рахуємо score для кожного спеціаліста
        agent_scores: List[Tuple[User, float]] = []

        for agent in agents:
            agent_expertise = expertise_profiles.get(agent.id, {})

            # Score = сума частот всіх збігаючихся ключових слів
            score = sum(agent_expertise.get(kw, 0) for kw in ticket_keywords)

            # Додаємо бонус за збіг зі спеціалізацією (specialty field)
            if agent.specialty:
                specialty_keywords = [
                    s.strip().lower() for s in agent.specialty.split(',')
                ]
                for ticket_kw in ticket_keywords:
                    if ticket_kw in specialty_keywords:
                        score += 10  # Бонус за збіг зі спеціалізацією

            # Враховуємо поточне навантаження (віднімаємо активні тікети)
            active_count = db.query(Ticket).filter(
                Ticket.assigned_to_user_id == agent.id,
                Ticket.status.in_([StatusEnum.NEW, StatusEnum.TRIAGE, StatusEnum.IN_PROGRESS])
            ).count()

            # Фінальний score: expertise_score - active_tickets * 2
            final_score = score - (active_count * 2)

            agent_scores.append((agent, final_score))

        # 5. Сортуємо за score та повертаємо найкращого
        if agent_scores:
            agent_scores.sort(key=lambda x: x[1], reverse=True)
            best_agent, best_score = agent_scores[0]

            # Якщо score позитивний, повертаємо спеціаліста
            if best_score > 0:
                return best_agent

        return None

    @staticmethod
    def get_specialist_stats(agent_id: int, db: Session) -> Dict:
        """
        Повертає статистику для спеціаліста:
        - Кількість вирішених тікетів загалом
        - Кількість вирішених тікетів по категоріях
        - Топ-10 ключових слів експертизи
        """
        # Вирішені тікети
        resolved_tickets = db.query(Ticket).filter(
            Ticket.assigned_to_user_id == agent_id,
            Ticket.status.in_([StatusEnum.RESOLVED, StatusEnum.CLOSED])
        ).all()

        total_resolved = len(resolved_tickets)

        # По категоріях
        by_category = defaultdict(int)
        for ticket in resolved_tickets:
            if ticket.category:
                by_category[ticket.category.value] += 1

        # Топ-10 ключових слів
        expertise_profiles = LearningService.build_expertise_profiles(db)
        agent_expertise = expertise_profiles.get(agent_id, {})

        top_keywords = sorted(
            agent_expertise.items(),
            key=lambda x: x[1],
            reverse=True
        )[:10]

        return {
            "total_resolved": total_resolved,
            "by_category": dict(by_category),
            "top_keywords": [{"keyword": kw, "count": cnt} for kw, cnt in top_keywords]
        }


learning_service = LearningService()
