"""
Швидкий seed тікетів БЕЗ LLM викликів.
Використовується для початкового навчання ML моделі.
"""
import sys
from datetime import datetime, timedelta
import random

from app.database import SessionLocal
from app.models.ticket import Ticket
from app.models.user import User
from app.models.department import Department
from app.core.enums import StatusEnum, PriorityEnum, CategoryEnum, RoleEnum


# Датасет IT Support тікетів
SAMPLE_TICKETS = [
    # P1 - Critical
    {"title": "Production server down", "description": "Main server crashed. All users affected. Revenue impact critical.", "priority": PriorityEnum.P1, "category": CategoryEnum.HARDWARE},
    {"title": "Database server offline", "description": "DB not responding. Data loss risk for last 2 hours.", "priority": PriorityEnum.P1, "category": CategoryEnum.SOFTWARE},
    {"title": "Security breach detected", "description": "Unauthorized access to admin panel from external IP.", "priority": PriorityEnum.P1, "category": CategoryEnum.NETWORK},
    {"title": "Email system down", "description": "Exchange server offline. 500+ users cannot send/receive email.", "priority": PriorityEnum.P1, "category": CategoryEnum.SOFTWARE},
    {"title": "Payment gateway failure", "description": "Customers cannot complete purchases. Direct revenue loss.", "priority": PriorityEnum.P1, "category": CategoryEnum.NETWORK},

    # P2 - High
    {"title": "VPN connection unstable", "description": "Remote workers experiencing frequent disconnections every 15 minutes.", "priority": PriorityEnum.P2, "category": CategoryEnum.NETWORK},
    {"title": "Printer offline 3rd floor", "description": "Main office printer not responding. Hardware check needed.", "priority": PriorityEnum.P2, "category": CategoryEnum.HARDWARE},
    {"title": "Software licenses expiring", "description": "Adobe CC licenses expire in 7 days for marketing team (15 users).", "priority": PriorityEnum.P2, "category": CategoryEnum.SOFTWARE},
    {"title": "File share access denied", "description": "Finance team cannot access \\\\server\\finance for month-end reports.", "priority": PriorityEnum.P2, "category": CategoryEnum.ACCESS},
    {"title": "Slow network Building B", "description": "Network speeds 10x slower than normal. Started this morning.", "priority": PriorityEnum.P2, "category": CategoryEnum.NETWORK},
    {"title": "CRM data not syncing", "description": "Salesforce showing 2-day-old customer data. Sales team impacted.", "priority": PriorityEnum.P2, "category": CategoryEnum.SOFTWARE},
    {"title": "Conference room HDMI broken", "description": "Room 5B display not connecting. Client presentation in 2 hours.", "priority": PriorityEnum.P2, "category": CategoryEnum.HARDWARE},

    # P3 - Standard
    {"title": "Keyboard replacement needed", "description": "Sticky keys on current keyboard. Request ergonomic replacement.", "priority": PriorityEnum.P3, "category": CategoryEnum.HARDWARE},
    {"title": "RAM upgrade for developer", "description": "Laptop slow with multiple IDEs. Upgrade from 16GB to 32GB requested.", "priority": PriorityEnum.P3, "category": CategoryEnum.HARDWARE},
    {"title": "Software access for new hire", "description": "New marketing employee needs Adobe Illustrator license. Starts next week.", "priority": PriorityEnum.P3, "category": CategoryEnum.ACCESS},
    {"title": "Calendar not syncing mobile", "description": "iPhone calendar not showing Outlook meetings. Desktop works fine.", "priority": PriorityEnum.P3, "category": CategoryEnum.SOFTWARE},
    {"title": "Request second monitor", "description": "Would improve productivity. Current setup has single screen.", "priority": PriorityEnum.P3, "category": CategoryEnum.HARDWARE},
    {"title": "Shared drive cleanup", "description": "Drive nearly full. Need help archiving files older than 3 years.", "priority": PriorityEnum.P3, "category": CategoryEnum.OTHER},
    {"title": "Browser homepage resetting", "description": "Chrome homepage changes to default on every restart. Minor issue.", "priority": PriorityEnum.P3, "category": CategoryEnum.SOFTWARE},
    {"title": "Wi-Fi password change request", "description": "Guest WiFi password should be rotated for security. Non-urgent.", "priority": PriorityEnum.P3, "category": CategoryEnum.NETWORK},
]


def seed_tickets_fast(count: int = 100, days_back: int = 30):
    """
    Створює тікети БЕЗ LLM викликів для швидкого seed.
    """
    db = SessionLocal()

    try:
        # Отримати користувачів та департаменти
        users = db.query(User).filter(User.role == RoleEnum.USER).all()
        agents = db.query(User).filter(User.role == RoleEnum.AGENT).all()
        departments = db.query(Department).all()

        if not users:
            print("ERROR: No users found. Run seed_data.py first!")
            return

        if not agents:
            print("ERROR: No agents found. Run seed_data.py first!")
            return

        if not departments:
            print("ERROR: No departments found. Run seed_data.py first!")
            return

        print(f"Creating {count} tickets without LLM (fast mode)...")
        print(f"Using {len(SAMPLE_TICKETS)} ticket templates\n")

        created_count = 0

        for i in range(count):
            # Випадковий темплейт
            template = random.choice(SAMPLE_TICKETS)

            # Випадкові дані
            user = random.choice(users)
            department = random.choice(departments)

            # Випадкова дата
            days_ago = random.randint(0, days_back)
            created_at = datetime.utcnow() - timedelta(days=days_ago)

            # Створити тікет БЕЗ ML/LLM
            ticket = Ticket(
                title=template["title"],
                description=template["description"],
                priority_manual=template["priority"],
                category=template["category"],
                status=StatusEnum.NEW,
                created_by_user_id=user.id,
                department_id=department.id,
                created_at=created_at,
                updated_at=created_at,
            )

            db.add(ticket)

            # 60% тікетів мають агента та змінений статус
            if random.random() < 0.6:
                ticket.assigned_to_user_id = random.choice(agents).id
                ticket.status = random.choice([
                    StatusEnum.IN_PROGRESS,
                    StatusEnum.TRIAGE,
                    StatusEnum.RESOLVED,
                ])

                if ticket.status == StatusEnum.RESOLVED:
                    ticket.resolved_at = created_at + timedelta(
                        hours=random.randint(1, 48)
                    )

            created_count += 1

            if created_count % 20 == 0:
                db.commit()
                print(f"  Created {created_count}/{count} tickets")

        db.commit()

        print(f"\nSuccessfully created {created_count} tickets!")
        print(f"\nPriority distribution:")

        p1 = db.query(Ticket).filter(Ticket.priority_manual == PriorityEnum.P1).count()
        p2 = db.query(Ticket).filter(Ticket.priority_manual == PriorityEnum.P2).count()
        p3 = db.query(Ticket).filter(Ticket.priority_manual == PriorityEnum.P3).count()

        print(f"  - P1 (Critical): {p1} ({p1/created_count*100:.1f}%)")
        print(f"  - P2 (High): {p2} ({p2/created_count*100:.1f}%)")
        print(f"  - P3 (Standard): {p3} ({p3/created_count*100:.1f}%)")

        print(f"\nCategory distribution:")
        for category in CategoryEnum:
            cat_count = db.query(Ticket).filter(Ticket.category == category).count()
            if cat_count > 0:
                print(f"  - {category.value}: {cat_count}")

        print(f"\nNext step: python train_initial_model.py")

    except Exception as e:
        print(f"ERROR: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    ticket_count = int(sys.argv[1]) if len(sys.argv) > 1 else 100
    days_range = int(sys.argv[2]) if len(sys.argv) > 2 else 30

    print("=" * 60)
    print("  Fast Ticket Seeding (No LLM)")
    print("  Creates tickets from templates")
    print("  Perfect for initial ML model training")
    print("=" * 60)
    print()

    seed_tickets_fast(count=ticket_count, days_back=days_range)
