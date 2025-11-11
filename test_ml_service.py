"""
Test ML service directly (no HTTP)
"""
from sqlalchemy.orm import Session
from app.database import SessionLocal, engine
from app.models.user import User
from app.models.department import Department
from app.schemas.ticket import TicketCreate
from app.services.ticket_service import ticket_service
from app.core.enums import PriorityEnum

# Create a database session
db = SessionLocal()

try:
    # Get admin user
    admin = db.query(User).filter(User.email == "admin@example.com").first()
    if not admin:
        print("[ERROR] Admin user not found")
        exit(1)

    print(f"[OK] Found user: {admin.email} (Role: {admin.role.value})")

    # Get department
    dept = db.query(Department).first()
    print(f"[OK] Found department: {dept.name} (ID: {dept.id})")

    # Create ticket
    print("\n[TEST] Creating ticket with ML prediction...")
    ticket_data = TicketCreate(
        title="Не працює комп'ютер",
        description="Комп'ютер не вмикається, чорний екран. Потрібна термінова допомога.",
        priority_manual=PriorityEnum.P3,
        department_id=dept.id,
    )

    ticket = ticket_service.create_ticket(
        ticket_data=ticket_data,
        creator=admin,
        db=db,
    )

    print(f"\n[SUCCESS] Ticket created!")
    print(f"  ID: {ticket.id}")
    print(f"  Incident ID: {ticket.incident_id}")
    print(f"  Title: {ticket.title}")
    print(f"  Status: {ticket.status.value}")
    print(f"  Priority (manual): {ticket.priority_manual.value}")
    print(f"  Priority (ML suggested): {ticket.priority_ml_suggested.value if ticket.priority_ml_suggested else None}")
    print(f"  Priority (ML confidence): {ticket.priority_ml_confidence}")
    print(f"  Category (ML suggested): {ticket.category_ml_suggested.value if ticket.category_ml_suggested else None}")
    print(f"  Category (ML confidence): {ticket.category_ml_confidence}")
    print(f"  Triage required: {ticket.triage_required}")
    print(f"  Triage reason: {ticket.triage_reason.value if ticket.triage_reason else None}")
    print(f"  Self-assign locked: {ticket.self_assign_locked}")
    print(f"  ML model version: {ticket.ml_model_version}")

finally:
    db.close()
