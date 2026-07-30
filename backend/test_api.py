import requests
import sys

# Login
login_data = {
    "username": "admin",
    "password": "Password123!"
}
print("Logging in...")
res_login = requests.post("http://localhost:8000/auth/login", data=login_data)
if res_login.status_code != 200:
    print(f"Login failed: {res_login.text}")
    sys.exit(1)

token = res_login.json()["access_token"]
headers = {"Authorization": f"Bearer {token}"}

payload = {
    "action": "delete_database",
    "record_count": 500,
    "external": False,
    "agent_id": "test_agent"
}

print("Testing /simulate API...")
res_sim = requests.post("http://localhost:8000/simulate/", json=payload, headers=headers)
print(f"/simulate Status Code: {res_sim.status_code}")
if res_sim.status_code != 200:
    print(res_sim.text)
    sys.exit(1)

print("Testing /execute API...")
res_exe = requests.post("http://localhost:8000/execute/", json=payload, headers=headers)
print(f"/execute Status Code: {res_exe.status_code}")
if res_exe.status_code != 200:
    print(res_exe.text)
    sys.exit(1)

print("All API tests passed!")
