"""
Seed агентів зі спеціалізаціями для Smart Assignment.

Створює агентів для кожного департаменту з різними спеціалізаціями:
- IT Support: VPN, Printers, Hardware, Software, Network
- Infrastructure: Servers, Databases, Storage, Backup
- Security: Firewall, Antivirus, Access Control
"""
import sys
from datetime import datetime
from app.database import SessionLocal
from app.models.user import User
from app.models.department import Department
from app.core.enums import RoleEnum
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# Спеціалізації для різних департаментів
AGENT_SPECIALTIES = {
    "IT Support": [
        {
            "name": "Alice Johnson",
            "email": "alice.johnson@company.com",
            "specialty": "VPN, Remote Access, Cisco AnyConnect, OpenVPN, Network Connectivity, SSL VPN",
            "workload_capacity": 15,
        },
        {
            "name": "Bob Martinez",
            "email": "bob.martinez@company.com",
            "specialty": "Printers, Scanners, HP, Canon, Epson, Print Queues, Driver Installation, Multifunction Devices",
            "workload_capacity": 20,
        },
        {
            "name": "Charlie Davis",
            "email": "charlie.davis@company.com",
            "specialty": "Workstation Hardware, Laptops, Desktop PC, RAM, Disk, Keyboard, Mouse, Monitor, PC Upgrades",
            "workload_capacity": 12,
        },
        {
            "name": "Diana Wilson",
            "email": "diana.wilson@company.com",
            "specialty": "Software Installation, Office 365, Adobe Creative Suite, Licensing, Updates, Activation",
            "workload_capacity": 18,
        },
        {
            "name": "Ethan Brown",
            "email": "ethan.brown@company.com",
            "specialty": "Local Network, Switches, VLAN, Ethernet, WiFi Access Points, Network Cables, LAN",
            "workload_capacity": 10,
        },
    ],
    "Network Team": [
        {
            "name": "Frank Miller",
            "email": "frank.miller@company.com",
            "specialty": "Network Infrastructure, Routers, Core Switches, WAN, MPLS, BGP, Network Design",
            "workload_capacity": 8,
        },
        {
            "name": "Grace Taylor",
            "email": "grace.taylor@company.com",
            "specialty": "Wireless Networks, WiFi 6, Access Points, Mesh Networks, Radio Frequency, Site Survey",
            "workload_capacity": 12,
        },
        {
            "name": "Henry Anderson",
            "email": "henry.anderson@company.com",
            "specialty": "Network Security, Firewall Configuration, VPN Tunnels, Network Segmentation, DMZ",
            "workload_capacity": 10,
        },
        {
            "name": "Iris Thomas",
            "email": "iris.thomas@company.com",
            "specialty": "Network Monitoring, Wireshark, SNMP, NetFlow, Performance Analysis, Troubleshooting",
            "workload_capacity": 15,
        },
    ],
    "Development": [
        {
            "name": "Maria Rodriguez",
            "email": "maria.rodriguez@company.com",
            "specialty": "CI/CD, Jenkins, GitLab CI, Docker, Kubernetes, DevOps, Build Pipeline, Automation",
            "workload_capacity": 12,
        },
        {
            "name": "Nathan Lee",
            "email": "nathan.lee@company.com",
            "specialty": "Version Control, Git, GitHub, Bitbucket, Code Review, Branching Strategies, Merge Conflicts",
            "workload_capacity": 20,
        },
        {
            "name": "Olivia Parker",
            "email": "olivia.parker@company.com",
            "specialty": "Cloud Infrastructure, AWS, Azure, GCP, Terraform, CloudFormation, Infrastructure as Code",
            "workload_capacity": 14,
        },
        {
            "name": "Peter Quinn",
            "email": "peter.quinn@company.com",
            "specialty": "Database Development, SQL, NoSQL, MongoDB, Redis, Database Optimization, Query Performance",
            "workload_capacity": 16,
        },
    ],
    "HR": [
        {
            "name": "Quinn Roberts",
            "email": "quinn.roberts@company.com",
            "specialty": "Employee Onboarding, New Hire Setup, Account Creation, Access Provisioning, Orientation",
            "workload_capacity": 18,
        },
        {
            "name": "Rachel Smith",
            "email": "rachel.smith@company.com",
            "specialty": "Payroll Systems, HR Software, Workday, SAP HR, Time Tracking, Benefits Administration",
            "workload_capacity": 15,
        },
        {
            "name": "Samuel Turner",
            "email": "samuel.turner@company.com",
            "specialty": "Employee Relations, Conflict Resolution, Performance Management, Policy Questions, Compliance",
            "workload_capacity": 12,
        },
        {
            "name": "Tina Underwood",
            "email": "tina.underwood@company.com",
            "specialty": "Recruitment, Applicant Tracking, Job Postings, Interview Scheduling, Candidate Management",
            "workload_capacity": 20,
        },
    ],
    "Finance": [
        {
            "name": "Uma Valdez",
            "email": "uma.valdez@company.com",
            "specialty": "Accounting Software, QuickBooks, SAP Finance, Oracle Financials, General Ledger, Invoicing",
            "workload_capacity": 14,
        },
        {
            "name": "Victor Wallace",
            "email": "victor.wallace@company.com",
            "specialty": "Expense Management, Travel Reimbursement, Receipt Processing, Budget Tracking, Cost Centers",
            "workload_capacity": 16,
        },
        {
            "name": "Wendy Xavier",
            "email": "wendy.xavier@company.com",
            "specialty": "Financial Reporting, Excel, Power BI, Data Analysis, Dashboards, KPI Tracking",
            "workload_capacity": 12,
        },
        {
            "name": "Xavier Young",
            "email": "xavier.young@company.com",
            "specialty": "Payment Processing, Wire Transfers, ACH, Credit Cards, Vendor Payments, Reconciliation",
            "workload_capacity": 18,
        },
    ],
}


def seed_agents_with_specialty(reset: bool = False):
    """
    Створює агентів зі спеціалізаціями.

    Args:
        reset: Якщо True - видаляє існуючих агентів перед створенням
    """
    db = SessionLocal()

    try:
        print("=" * 70)
        print("  Seed Agents with Specializations")
        print("  Creates IT support agents with different expertise areas")
        print("=" * 70)
        print()

        # Отримати всі департаменти
        departments = {d.name: d for d in db.query(Department).all()}

        if not departments:
            print("ERROR: No departments found!")
            print("Run seed_data.py first to create departments.")
            return

        print(f"Found {len(departments)} departments:")
        for dept_name in departments.keys():
            print(f"  - {dept_name}")
        print()

        # Опціонально видалити існуючих агентів
        if reset:
            existing_agents = db.query(User).filter(User.role == RoleEnum.AGENT).all()
            if existing_agents:
                print(f"RESET MODE: Deleting {len(existing_agents)} existing agents...")
                for agent in existing_agents:
                    db.delete(agent)
                db.commit()
                print("Deleted all existing agents.\n")

        # Створити агентів для кожного департаменту
        total_created = 0
        default_password = "agent123"  # Для тестування
        hashed_password = pwd_context.hash(default_password)

        for dept_name, agents_data in AGENT_SPECIALTIES.items():
            if dept_name not in departments:
                print(f"WARNING: Department '{dept_name}' not found in database. Skipping.")
                continue

            dept = departments[dept_name]
            print(f"Creating agents for {dept_name}:")

            for agent_data in agents_data:
                # Перевірити чи вже існує
                existing = db.query(User).filter(User.email == agent_data["email"]).first()
                if existing:
                    print(f"  SKIP: {agent_data['name']} ({agent_data['email']}) - already exists")
                    continue

                # Створити агента
                agent = User(
                    email=agent_data["email"],
                    hashed_password=hashed_password,
                    full_name=agent_data["name"],
                    role=RoleEnum.AGENT,
                    department_id=dept.id,
                    specialty=agent_data["specialty"],
                    workload_capacity=agent_data["workload_capacity"],
                    assignment_score=0.0,  # Початково 0, зростатиме з досвідом
                    availability_status="AVAILABLE",
                    is_active=True,
                )

                db.add(agent)
                total_created += 1

                # Показати спеціалізацію (перші 60 символів)
                specialty_preview = agent_data["specialty"][:60]
                if len(agent_data["specialty"]) > 60:
                    specialty_preview += "..."

                print(f"  + {agent_data['name']}")
                print(f"    Email: {agent_data['email']}")
                print(f"    Specialty: {specialty_preview}")
                print(f"    Capacity: {agent_data['workload_capacity']} tickets")

            print()

        db.commit()

        print("=" * 70)
        print(f"Successfully created {total_created} agents with specializations!")
        print()
        print("Agent credentials (for testing):")
        print(f"  Password for all agents: {default_password}")
        print()

        # Статистика
        print("Agents by department:")
        for dept_name, dept in departments.items():
            agent_count = db.query(User).filter(
                User.department_id == dept.id,
                User.role == RoleEnum.AGENT
            ).count()
            if agent_count > 0:
                print(f"  - {dept_name}: {agent_count} agents")

        print()
        print("Total agents in system:", db.query(User).filter(User.role == RoleEnum.AGENT).count())
        print()
        print("Next steps:")
        print("  1. Test Smart Assignment: Create tickets and see automatic assignment")
        print("  2. View agents: http://localhost:8000/ui_llm_static/board.html")
        print("  3. Seed tickets: python seed_tickets_fast.py 50")

    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    reset_mode = "--reset" in sys.argv or "-r" in sys.argv

    if reset_mode:
        print("WARNING: Running in RESET mode - will delete existing agents!")
        response = input("Continue? (yes/no): ")
        if response.lower() != "yes":
            print("Cancelled.")
            sys.exit(0)

    seed_agents_with_specialty(reset=reset_mode)
