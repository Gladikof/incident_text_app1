"""
Скрипт для додавання спеціалістів до бази даних
"""
from app.database import SessionLocal
from app.models import User, Department
from app.core.enums import RoleEnum
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def add_specialists():
    db = SessionLocal()
    try:
        # Отримуємо департаменти
        it_dept = db.query(Department).filter(Department.name == "IT Support").first()
        hr_dept = db.query(Department).filter(Department.name == "HR").first()
        finance_dept = db.query(Department).filter(Department.name == "Finance").first()

        if not it_dept:
            it_dept = Department(name="IT Support", description="Technical support department")
            db.add(it_dept)
            db.flush()

        if not hr_dept:
            hr_dept = Department(name="HR", description="Human resources department")
            db.add(hr_dept)
            db.flush()

        if not finance_dept:
            finance_dept = Department(name="Finance", description="Finance department")
            db.add(finance_dept)
            db.flush()

        # Спеціалісти IT Support (Hardware, Software, Network experts)
        specialists = [
            # IT Support - Hardware specialists
            {
                "email": "john.hardware@example.com",
                "full_name": "John Hardware",
                "role": RoleEnum.AGENT,
                "department_id": it_dept.id,
                "password": "agent123"
            },
            {
                "email": "alice.hardware@example.com",
                "full_name": "Alice Hardware",
                "role": RoleEnum.AGENT,
                "department_id": it_dept.id,
                "password": "agent123"
            },
            # IT Support - Software specialists
            {
                "email": "bob.software@example.com",
                "full_name": "Bob Software",
                "role": RoleEnum.AGENT,
                "department_id": it_dept.id,
                "password": "agent123"
            },
            {
                "email": "maria.software@example.com",
                "full_name": "Maria Software",
                "role": RoleEnum.AGENT,
                "department_id": it_dept.id,
                "password": "agent123"
            },
            # IT Support - Network specialists
            {
                "email": "tom.network@example.com",
                "full_name": "Tom Network",
                "role": RoleEnum.AGENT,
                "department_id": it_dept.id,
                "password": "agent123"
            },
            {
                "email": "sarah.network@example.com",
                "full_name": "Sarah Network",
                "role": RoleEnum.AGENT,
                "department_id": it_dept.id,
                "password": "agent123"
            },
            # IT Support - Access specialists
            {
                "email": "david.access@example.com",
                "full_name": "David Access",
                "role": RoleEnum.AGENT,
                "department_id": it_dept.id,
                "password": "agent123"
            },
            {
                "email": "emma.access@example.com",
                "full_name": "Emma Access",
                "role": RoleEnum.AGENT,
                "department_id": it_dept.id,
                "password": "agent123"
            },
            # HR specialists
            {
                "email": "kate.hr@example.com",
                "full_name": "Kate HR Specialist",
                "role": RoleEnum.AGENT,
                "department_id": hr_dept.id,
                "password": "agent123"
            },
            {
                "email": "mike.hr@example.com",
                "full_name": "Mike HR Specialist",
                "role": RoleEnum.AGENT,
                "department_id": hr_dept.id,
                "password": "agent123"
            },
            # Finance specialists
            {
                "email": "anna.finance@example.com",
                "full_name": "Anna Finance",
                "role": RoleEnum.AGENT,
                "department_id": finance_dept.id,
                "password": "agent123"
            },
            {
                "email": "peter.finance@example.com",
                "full_name": "Peter Finance",
                "role": RoleEnum.AGENT,
                "department_id": finance_dept.id,
                "password": "agent123"
            },
        ]

        added_count = 0
        for spec_data in specialists:
            # Перевіряємо чи вже існує
            existing = db.query(User).filter(User.email == spec_data["email"]).first()
            if not existing:
                user = User(
                    email=spec_data["email"],
                    full_name=spec_data["full_name"],
                    hashed_password=pwd_context.hash(spec_data["password"]),
                    role=spec_data["role"],
                    department_id=spec_data["department_id"],
                    is_active=True
                )
                db.add(user)
                added_count += 1
                print(f"[+] Додано: {spec_data['full_name']} ({spec_data['email']})")
            else:
                print(f"[=] Вже існує: {spec_data['email']}")

        db.commit()
        print(f"\n[OK] Успішно додано {added_count} нових спеціалістів!")
        print(f"[INFO] Всього користувачів: {db.query(User).count()}")

    except Exception as e:
        print(f"[ERROR] Помилка: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    add_specialists()
