"""
Seed script для тестових даних
"""
from app.database import SessionLocal
from app.models.user import User
from app.models.department import Department
from app.models.settings import SystemSettings
from app.core.security import get_password_hash
from app.core.enums import RoleEnum


def seed_database():
    """Створити тестові дані"""
    db = SessionLocal()

    try:
        # 1. Системні налаштування
        settings = SystemSettings.get_settings(db)
        print(f"[SEED] System settings created: {settings}")

        # 2. Департаменти
        departments = [
            Department(name="IT Support", description="Technical support team"),
            Department(name="Network Team", description="Network infrastructure"),
            Department(name="Development", description="Software development"),
        ]

        for dept in departments:
            existing = db.query(Department).filter(Department.name == dept.name).first()
            if not existing:
                db.add(dept)
        db.commit()
        print(f"[SEED] Departments created: {len(departments)}")

        # Отримати ID департаментів
        it_dept = db.query(Department).filter(Department.name == "IT Support").first()
        net_dept = db.query(Department).filter(Department.name == "Network Team").first()

        # 3. Користувачі
        users = [
            {
                "email": "admin@example.com",
                "password": "admin123",
                "full_name": "Admin User",
                "role": RoleEnum.ADMIN,
                "is_lead": False,
                "department_id": None,
            },
            {
                "email": "lead@example.com",
                "password": "lead123",
                "full_name": "Lead Manager",
                "role": RoleEnum.LEAD,
                "is_lead": True,
                "department_id": it_dept.id if it_dept else None,
            },
            {
                "email": "agent1@example.com",
                "password": "agent123",
                "full_name": "Agent Smith",
                "role": RoleEnum.AGENT,
                "is_lead": False,
                "department_id": it_dept.id if it_dept else None,
            },
            {
                "email": "agent2@example.com",
                "password": "agent123",
                "full_name": "Agent Johnson",
                "role": RoleEnum.AGENT,
                "is_lead": False,
                "department_id": net_dept.id if net_dept else None,
            },
            {
                "email": "user@example.com",
                "password": "user123",
                "full_name": "Regular User",
                "role": RoleEnum.USER,
                "is_lead": False,
                "department_id": None,
            },
        ]

        for user_data in users:
            existing = db.query(User).filter(User.email == user_data["email"]).first()
            if not existing:
                new_user = User(
                    email=user_data["email"],
                    hashed_password=get_password_hash(user_data["password"]),
                    full_name=user_data["full_name"],
                    role=user_data["role"],
                    is_lead=user_data["is_lead"],
                    department_id=user_data["department_id"],
                )
                db.add(new_user)

        db.commit()
        print(f"[SEED] Users created: {len(users)}")

        print("\n=== Seed Data Created Successfully! ===")
        print("\nTest Credentials:")
        print("  Admin:  admin@example.com / admin123")
        print("  Lead:   lead@example.com / lead123")
        print("  Agent1: agent1@example.com / agent123")
        print("  Agent2: agent2@example.com / agent123")
        print("  User:   user@example.com / user123")
        print("\nRun server: uvicorn app.main:app --reload --port 8000")

    except Exception as e:
        print(f"[ERROR] Seed failed: {e}")
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    seed_database()
