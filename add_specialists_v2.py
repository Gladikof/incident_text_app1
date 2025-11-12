"""
Скрипт для додавання спеціалістів з детальними спеціалізаціями (версія 2)
Тепер по 3 спеціалісти на категорію з конкретними під-спеціалізаціями
"""
from app.database import SessionLocal
from app.models import User, Department
from app.core.enums import RoleEnum
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def add_specialists_v2():
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

        # Спеціалісти з детальними спеціалізаціями
        specialists = [
            # === HARDWARE SPECIALISTS (3) ===
            {
                "email": "john.hardware@example.com",
                "full_name": "John Desktop Hardware",
                "role": RoleEnum.AGENT,
                "department_id": it_dept.id,
                "password": "agent123",
                "specialty": "Desktop,Workstation,PC Assembly,RAM,HDD,SSD,Motherboard,GPU"
            },
            {
                "email": "alice.hardware@example.com",
                "full_name": "Alice Laptop Hardware",
                "role": RoleEnum.AGENT,
                "department_id": it_dept.id,
                "password": "agent123",
                "specialty": "Laptop,Notebook,Battery,Screen,Keyboard,Touchpad"
            },
            {
                "email": "mike.hardware@example.com",
                "full_name": "Mike Peripheral Hardware",
                "role": RoleEnum.AGENT,
                "department_id": it_dept.id,
                "password": "agent123",
                "specialty": "Printer,Scanner,Monitor,Mouse,Keyboard,Peripheral,USB"
            },

            # === SOFTWARE SPECIALISTS (3) ===
            {
                "email": "bob.software@example.com",
                "full_name": "Bob Windows Software",
                "role": RoleEnum.AGENT,
                "department_id": it_dept.id,
                "password": "agent123",
                "specialty": "Windows,OS,Microsoft Office,Excel,Word,PowerPoint,Outlook"
            },
            {
                "email": "maria.software@example.com",
                "full_name": "Maria Application Software",
                "role": RoleEnum.AGENT,
                "department_id": it_dept.id,
                "password": "agent123",
                "specialty": "Application,Install,1C,SAP,CRM,ERP,Database,SQL"
            },
            {
                "email": "anna.software@example.com",
                "full_name": "Anna License Software",
                "role": RoleEnum.AGENT,
                "department_id": it_dept.id,
                "password": "agent123",
                "specialty": "License,Activation,Subscription,Software Update,Antivirus"
            },

            # === NETWORK SPECIALISTS (3) ===
            {
                "email": "tom.network@example.com",
                "full_name": "Tom VPN Network",
                "role": RoleEnum.AGENT,
                "department_id": it_dept.id,
                "password": "agent123",
                "specialty": "VPN,Remote Access,Cisco AnyConnect,OpenVPN,IPsec,Firewall"
            },
            {
                "email": "sarah.network@example.com",
                "full_name": "Sarah LAN Network",
                "role": RoleEnum.AGENT,
                "department_id": it_dept.id,
                "password": "agent123",
                "specialty": "Local Network,LAN,Switch,Router,VLAN,Cable,Ethernet,RJ45"
            },
            {
                "email": "peter.network@example.com",
                "full_name": "Peter WiFi Network",
                "role": RoleEnum.AGENT,
                "department_id": it_dept.id,
                "password": "agent123",
                "specialty": "WiFi,Wireless,Access Point,SSID,Wi-Fi Password,Signal"
            },

            # === ACCESS SPECIALISTS (3) ===
            {
                "email": "david.access@example.com",
                "full_name": "David Password Access",
                "role": RoleEnum.AGENT,
                "department_id": it_dept.id,
                "password": "agent123",
                "specialty": "Password,Password Reset,Account Unlock,Login,Credentials"
            },
            {
                "email": "emma.access@example.com",
                "full_name": "Emma Permission Access",
                "role": RoleEnum.AGENT,
                "department_id": it_dept.id,
                "password": "agent123",
                "specialty": "Permission,Access Rights,File Share,Folder Access,AD Group"
            },
            {
                "email": "kate.access@example.com",
                "full_name": "Kate System Access",
                "role": RoleEnum.AGENT,
                "department_id": it_dept.id,
                "password": "agent123",
                "specialty": "System Access,Application Access,Database Access,Server Access"
            },

            # === HR SPECIALISTS (3) ===
            {
                "email": "julia.hr@example.com",
                "full_name": "Julia HR Recruitment",
                "role": RoleEnum.AGENT,
                "department_id": hr_dept.id,
                "password": "agent123",
                "specialty": "Recruitment,Hiring,Interview,Onboarding,Job Posting"
            },
            {
                "email": "mark.hr@example.com",
                "full_name": "Mark HR Benefits",
                "role": RoleEnum.AGENT,
                "department_id": hr_dept.id,
                "password": "agent123",
                "specialty": "Benefits,Salary,Vacation,Leave,Insurance,Compensation"
            },
            {
                "email": "lisa.hr@example.com",
                "full_name": "Lisa HR Training",
                "role": RoleEnum.AGENT,
                "department_id": hr_dept.id,
                "password": "agent123",
                "specialty": "Training,Development,Course,Education,Certification"
            },

            # === FINANCE SPECIALISTS (3) ===
            {
                "email": "george.finance@example.com",
                "full_name": "George Finance Accounting",
                "role": RoleEnum.AGENT,
                "department_id": finance_dept.id,
                "password": "agent123",
                "specialty": "Accounting,Invoice,Payment,Expense,Receipt,Transaction"
            },
            {
                "email": "sophia.finance@example.com",
                "full_name": "Sophia Finance Budget",
                "role": RoleEnum.AGENT,
                "department_id": finance_dept.id,
                "password": "agent123",
                "specialty": "Budget,Planning,Forecast,Cost,Allocation,Financial Report"
            },
            {
                "email": "daniel.finance@example.com",
                "full_name": "Daniel Finance Procurement",
                "role": RoleEnum.AGENT,
                "department_id": finance_dept.id,
                "password": "agent123",
                "specialty": "Procurement,Purchase,Vendor,Contract,Order,Supplier"
            },
        ]

        added_count = 0
        updated_count = 0
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
                    specialty=spec_data.get("specialty"),
                    is_active=True
                )
                db.add(user)
                added_count += 1
                print(f"[+] Додано: {spec_data['full_name']} ({spec_data['email']})")
                print(f"    Спеціалізація: {spec_data.get('specialty', 'N/A')}")
            else:
                # Оновлюємо спеціалізацію для існуючих користувачів
                if spec_data.get("specialty") and existing.specialty != spec_data["specialty"]:
                    existing.specialty = spec_data["specialty"]
                    updated_count += 1
                    print(f"[~] Оновлено спеціалізацію: {spec_data['full_name']}")
                    print(f"    Нова спеціалізація: {spec_data['specialty']}")
                else:
                    print(f"[=] Вже існує: {spec_data['email']}")

        db.commit()
        print(f"\n[OK] Успішно додано {added_count} нових спеціалістів!")
        print(f"[OK] Оновлено спеціалізацію для {updated_count} існуючих спеціалістів!")
        print(f"[INFO] Всього користувачів: {db.query(User).count()}")

        # Статистика по департаментах
        it_agents = db.query(User).filter(
            User.department_id == it_dept.id,
            User.role == RoleEnum.AGENT
        ).count()
        hr_agents = db.query(User).filter(
            User.department_id == hr_dept.id,
            User.role == RoleEnum.AGENT
        ).count()
        finance_agents = db.query(User).filter(
            User.department_id == finance_dept.id,
            User.role == RoleEnum.AGENT
        ).count()

        print(f"[INFO] IT Support агентів: {it_agents}")
        print(f"[INFO] HR агентів: {hr_agents}")
        print(f"[INFO] Finance агентів: {finance_agents}")

    except Exception as e:
        print(f"[ERROR] Помилка: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    add_specialists_v2()
