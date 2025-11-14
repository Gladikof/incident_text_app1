"""
Smart Assignment Service - інтелектуальний вибір виконавця для тікетів.

Hybrid Approach:
1. LLM suggestion (team + preferred skills)
2. Smart Service (workload, availability, skills matching)
3. Historical performance analysis
4. Weighted voting для фінального рішення
"""
import json
from typing import List, Dict, Optional, Tuple
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func, and_

from app.models.user import User
from app.models.ticket import Ticket
from app.core.enums import StatusEnum, RoleEnum


class SmartAssignmentService:
    """
    Сервіс для Smart Assignment - вибір найкращого виконавця.
    """

    # Ваги для hybrid decision
    LLM_WEIGHT = 0.30           # LLM suggestion
    SKILL_MATCH_WEIGHT = 0.25   # Skill matching score
    WORKLOAD_WEIGHT = 0.20      # Workload balance
    PERFORMANCE_WEIGHT = 0.15   # Historical performance
    AVAILABILITY_WEIGHT = 0.10  # Availability status

    # Пороги
    MIN_CONFIDENCE_THRESHOLD = 0.50  # Мінімальна впевненість для auto-assignment
    HIGH_CONFIDENCE_THRESHOLD = 0.75 # Висока впевненість

    @staticmethod
    def find_best_assignee(
        ticket_text: str,
        priority: str,
        category: str,
        department_id: Optional[int],
        llm_team: Optional[str],
        llm_assignee: Optional[str],
        db: Session,
    ) -> Dict:
        """
        Головний метод: знаходить найкращого виконавця використовуючи hybrid approach.

        Args:
            ticket_text: Повний текст тікета (title + description)
            priority: P1, P2, P3
            category: HARDWARE, SOFTWARE, NETWORK, etc.
            department_id: ID департаменту
            llm_team: Team suggestion від LLM
            llm_assignee: Assignee suggestion від LLM (може бути None)
            db: Database session

        Returns:
            Dict з полями:
                - assignee_id: ID обраного agent (або None)
                - confidence: Confidence score (0-1)
                - method: "HYBRID", "LLM_ONLY", "SMART_SERVICE"
                - reasoning: Пояснення рішення
                - alternatives: List[Dict] топ-3 кандидатів
        """

        # 1. Отримуємо список потенційних candidates
        candidates = SmartAssignmentService._get_candidate_agents(
            department_id=department_id,
            llm_team=llm_team,
            db=db
        )

        if not candidates:
            return {
                "assignee_id": None,
                "confidence": 0.0,
                "method": "NO_CANDIDATES",
                "reasoning": "Немає доступних агентів у вказаному департаменті/команді",
                "alternatives": [],
            }

        # 2. Рахуємо scores для кожного кандидата
        scored_candidates = []
        for agent in candidates:
            scores = SmartAssignmentService._calculate_agent_scores(
                agent=agent,
                ticket_text=ticket_text,
                priority=priority,
                category=category,
                llm_assignee=llm_assignee,
                db=db,
            )

            # Weighted sum
            final_score = (
                scores["llm_match"] * SmartAssignmentService.LLM_WEIGHT +
                scores["skill_match"] * SmartAssignmentService.SKILL_MATCH_WEIGHT +
                scores["workload"] * SmartAssignmentService.WORKLOAD_WEIGHT +
                scores["performance"] * SmartAssignmentService.PERFORMANCE_WEIGHT +
                scores["availability"] * SmartAssignmentService.AVAILABILITY_WEIGHT
            )

            scored_candidates.append({
                "agent": agent,
                "final_score": final_score,
                "scores_breakdown": scores,
            })

        # 3. Сортуємо за final_score (найкращий = найвищий score)
        scored_candidates.sort(key=lambda x: x["final_score"], reverse=True)

        # 4. Беремо топ-1 як фінальне рішення
        best = scored_candidates[0]
        best_agent = best["agent"]
        confidence = best["final_score"]

        # 5. Визначаємо method
        method = SmartAssignmentService._determine_method(
            llm_assignee=llm_assignee,
            best_agent_id=best_agent.id,
            confidence=confidence,
        )

        # 6. Генеруємо reasoning
        reasoning = SmartAssignmentService._generate_reasoning(
            agent=best_agent,
            scores=best["scores_breakdown"],
            confidence=confidence,
            method=method,
        )

        # 7. Формуємо alternatives (топ-3)
        alternatives = [
            {
                "agent_id": c["agent"].id,
                "agent_name": c["agent"].full_name,
                "score": round(c["final_score"], 3),
                "skill_match": round(c["scores_breakdown"]["skill_match"], 2),
                "workload": round(c["scores_breakdown"]["workload"], 2),
            }
            for c in scored_candidates[:3]
        ]

        return {
            "assignee_id": best_agent.id,
            "confidence": round(confidence, 3),
            "method": method,
            "reasoning": reasoning,
            "alternatives": alternatives,
        }

    @staticmethod
    def _get_candidate_agents(
        department_id: Optional[int],
        llm_team: Optional[str],
        db: Session,
    ) -> List[User]:
        """
        Отримує список потенційних candidates для assignment.

        Фільтри:
        - Role = AGENT або LEAD
        - is_active = True
        - availability_status != OFFLINE, ON_LEAVE
        - Department matching (якщо є)
        """

        query = db.query(User).filter(
            User.role.in_([RoleEnum.AGENT, RoleEnum.LEAD]),
            User.is_active == True,
            User.availability_status.notin_(["OFFLINE", "ON_LEAVE"])
        )

        # Якщо department вказано - фільтруємо
        if department_id:
            query = query.filter(User.department_id == department_id)

        # TODO: Фільтр за llm_team якщо потрібно (наразі не реалізовано)

        candidates = query.all()
        return candidates

    @staticmethod
    def _calculate_agent_scores(
        agent: User,
        ticket_text: str,
        priority: str,
        category: str,
        llm_assignee: Optional[str],
        db: Session,
    ) -> Dict[str, float]:
        """
        Рахує всі scores для одного agent.

        Returns:
            Dict з scores (всі від 0 до 1):
                - llm_match: Чи співпадає з LLM suggestion
                - skill_match: TF-IDF similarity між specialty і ticket_text
                - workload: Inverse workload (менше тікетів = краще)
                - performance: Historical assignment_score
                - availability: Availability bonus
        """

        # 1. LLM Match
        llm_match = 1.0 if llm_assignee and str(agent.id) == str(llm_assignee) else 0.0

        # 2. Skill Match (TF-IDF similarity)
        skill_match = SmartAssignmentService._calculate_skill_match(
            agent_specialty=agent.specialty,
            ticket_text=ticket_text,
        )

        # 3. Workload Score
        workload_score = SmartAssignmentService._calculate_workload_score(
            agent_id=agent.id,
            workload_capacity=agent.workload_capacity,
            db=db,
        )

        # 4. Performance Score (historical)
        performance = agent.assignment_score  # Вже normalized (0-1)

        # 5. Availability Score
        availability_map = {
            "AVAILABLE": 1.0,
            "BUSY": 0.5,
            "OFFLINE": 0.0,
            "ON_LEAVE": 0.0,
        }
        availability = availability_map.get(agent.availability_status, 0.5)

        return {
            "llm_match": llm_match,
            "skill_match": skill_match,
            "workload": workload_score,
            "performance": performance,
            "availability": availability,
        }

    @staticmethod
    def _calculate_skill_match(
        agent_specialty: Optional[str],
        ticket_text: str,
    ) -> float:
        """
        Рахує similarity між agent specialty і ticket text.

        Проста реалізація: keyword matching.
        Для production можна використати TF-IDF або embeddings.

        Returns:
            Score від 0 до 1
        """

        if not agent_specialty or not ticket_text:
            return 0.0

        # Lowercase для порівняння
        specialty_lower = agent_specialty.lower()
        ticket_lower = ticket_text.lower()

        # Розбиваємо specialty на keywords
        keywords = [kw.strip() for kw in specialty_lower.split(",")]

        # Рахуємо скільки keywords є в ticket_text
        matches = sum(1 for kw in keywords if kw in ticket_lower)

        # Normalize: matches / total keywords
        if len(keywords) == 0:
            return 0.0

        return min(matches / len(keywords), 1.0)

    @staticmethod
    def _calculate_workload_score(
        agent_id: int,
        workload_capacity: int,
        db: Session,
    ) -> float:
        """
        Рахує workload score: чим менше активних тікетів, тим краще.

        Returns:
            Score від 0 до 1 (1 = немає тікетів, 0 = перевантажений)
        """

        # Рахуємо скільки NEW/TRIAGE/IN_PROGRESS тікетів у agent
        active_tickets = db.query(func.count(Ticket.id)).filter(
            Ticket.assigned_to_user_id == agent_id,
            Ticket.status.in_([StatusEnum.NEW, StatusEnum.TRIAGE, StatusEnum.IN_PROGRESS])
        ).scalar()

        if active_tickets >= workload_capacity:
            return 0.0  # Перевантажений

        # Inverse: чим менше тікетів, тим вищий score
        return 1.0 - (active_tickets / workload_capacity)

    @staticmethod
    def _determine_method(
        llm_assignee: Optional[str],
        best_agent_id: int,
        confidence: float,
    ) -> str:
        """
        Визначає яким методом було обрано assignee.

        Returns:
            "HYBRID", "LLM_ONLY", "SMART_SERVICE"
        """

        if llm_assignee and str(best_agent_id) == str(llm_assignee):
            # LLM та Smart Service погодились
            if confidence >= SmartAssignmentService.HIGH_CONFIDENCE_THRESHOLD:
                return "HYBRID"  # Високий confidence
            else:
                return "LLM_ONLY"  # LLM suggestion але низький confidence

        # Smart Service overrode LLM
        return "SMART_SERVICE"

    @staticmethod
    def _generate_reasoning(
        agent: User,
        scores: Dict[str, float],
        confidence: float,
        method: str,
    ) -> str:
        """
        Генерує human-readable пояснення чому було обрано цього agent.
        """

        reasons = []

        # Top factor
        top_factor = max(scores, key=scores.get)
        top_value = scores[top_factor]

        factor_names = {
            "llm_match": "LLM recommendation",
            "skill_match": "Skill matching",
            "workload": "Workload balance",
            "performance": "Historical performance",
            "availability": "Availability",
        }

        reasons.append(
            f"Selected {agent.full_name} ({agent.email}) "
            f"with confidence {confidence:.2f} using {method} approach."
        )

        reasons.append(
            f"Top factor: {factor_names.get(top_factor, top_factor)} ({top_value:.2f})."
        )

        # Skill match details
        if scores["skill_match"] > 0.5:
            reasons.append(f"Strong skill match based on specialty: {agent.specialty}.")

        # Workload info
        if scores["workload"] > 0.7:
            reasons.append("Low current workload - agent is available.")
        elif scores["workload"] < 0.3:
            reasons.append("Agent has high workload but was still best match.")

        return " ".join(reasons)

    @staticmethod
    def update_agent_performance(
        agent_id: int,
        was_confirmed: bool,
        resolution_time_hours: Optional[float],
        db: Session,
    ):
        """
        Оновлює assignment_score agent на основі feedback.

        Args:
            agent_id: ID agent
            was_confirmed: True якщо assignment був підтверджений
            resolution_time_hours: Час вирішення тікета (години)
            db: Database session
        """

        agent = db.query(User).filter(User.id == agent_id).first()
        if not agent:
            return

        # Простий алгоритм оновлення score
        current_score = agent.assignment_score

        # Якщо підтверджено - збільшуємо
        if was_confirmed:
            delta = 0.05
        else:
            delta = -0.05

        # Бонус за швидке вирішення
        if resolution_time_hours is not None and resolution_time_hours < 24:
            delta += 0.02

        # Оновлюємо з moving average (exponential smoothing)
        new_score = current_score * 0.9 + (current_score + delta) * 0.1

        # Clip до [0, 1]
        agent.assignment_score = max(0.0, min(1.0, new_score))

        db.commit()


smart_assignment_service = SmartAssignmentService()
