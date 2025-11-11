"""
Test script for ticket creation with ML prediction
"""
import requests
import json

BASE_URL = "http://127.0.0.1:8002"

# 1. Login
print("1. Logging in...")
login_response = requests.post(
    f"{BASE_URL}/auth/login/json",
    json={"email": "admin@example.com", "password": "admin123"}
)
token = login_response.json()["access_token"]
print(f"   Token acquired: {token[:20]}...")

headers = {"Authorization": f"Bearer {token}"}

# 2. Create ticket with ML prediction
print("\n2. Creating ticket with ML prediction...")
ticket_data = {
    "title": "Не працює комп'ютер",
    "description": "Комп'ютер не вмикається, чорний екран. Потрібна термінова допомога.",
    "priority_manual": "P3",
    "department_id": 1
}

create_response = requests.post(
    f"{BASE_URL}/tickets",
    json=ticket_data,
    headers=headers
)

if create_response.status_code == 201:
    ticket = create_response.json()
    print("   [OK] Ticket created successfully!")
    print(f"   ID: {ticket['id']}")
    print(f"   Incident ID: {ticket['incident_id']}")
    print(f"   Status: {ticket['status']}")
    print(f"   Priority (manual): {ticket['priority_manual']}")
    print(f"   Priority (ML suggested): {ticket.get('priority_ml_suggested')}")
    print(f"   Priority (ML confidence): {ticket.get('priority_ml_confidence')}")
    print(f"   Category (ML suggested): {ticket.get('category_ml_suggested')}")
    print(f"   Category (ML confidence): {ticket.get('category_ml_confidence')}")
    print(f"   Triage required: {ticket.get('triage_required')}")
    print(f"   Triage reason: {ticket.get('triage_reason')}")

    ticket_id = ticket['id']

    # 3. Get ticket details
    print(f"\n3. Getting ticket details...")
    get_response = requests.get(
        f"{BASE_URL}/tickets/{ticket_id}",
        headers=headers
    )
    if get_response.status_code == 200:
        print("   [OK] Ticket retrieved successfully!")

    # 4. List all tickets
    print(f"\n4. Listing all tickets...")
    list_response = requests.get(
        f"{BASE_URL}/tickets",
        headers=headers
    )
    if list_response.status_code == 200:
        tickets = list_response.json()
        print(f"   [OK] Found {len(tickets)} ticket(s)")
        for t in tickets:
            print(f"      - {t['incident_id']}: {t['title']} (Status: {t['status']}, Priority: {t['priority_manual']})")

else:
    print(f"   [ERROR] Creating ticket failed: {create_response.status_code}")
    print(f"   {create_response.text}")
