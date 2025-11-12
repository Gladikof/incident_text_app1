"""
Test JWT auth fix
"""
import requests

BASE_URL = "http://127.0.0.1:8002"

# 1. Login
print("1. Testing login...")
response = requests.post(
    f"{BASE_URL}/auth/login/json",
    json={"email": "admin@example.com", "password": "admin123"}
)
print(f"   Status: {response.status_code}")
if response.status_code == 200:
    data = response.json()
    token = data["access_token"]
    print(f"   Token: {token[:50]}...")

    # 2. Test /auth/me
    print("\n2. Testing /auth/me...")
    me_response = requests.get(
        f"{BASE_URL}/auth/me",
        headers={"Authorization": f"Bearer {token}"}
    )
    print(f"   Status: {me_response.status_code}")
    if me_response.status_code == 200:
        user = me_response.json()
        print(f"   [OK] User: {user['email']} ({user['role']})")
    else:
        print(f"   [ERROR] {me_response.text}")

    # 3. Test getting tickets
    print("\n3. Testing GET /tickets...")
    tickets_response = requests.get(
        f"{BASE_URL}/tickets",
        headers={"Authorization": f"Bearer {token}"}
    )
    print(f"   Status: {tickets_response.status_code}")
    if tickets_response.status_code == 200:
        tickets = tickets_response.json()
        print(f"   [OK] Found {len(tickets)} ticket(s)")
        for t in tickets:
            print(f"      - {t['incident_id']}: {t['title']}")
    else:
        print(f"   [ERROR] {tickets_response.text}")
else:
    print(f"   [ERROR] Login failed: {response.text}")
