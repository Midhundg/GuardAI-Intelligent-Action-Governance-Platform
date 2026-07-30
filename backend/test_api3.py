import requests
import sys

login_data = {"username": "admin", "password": "Password123!"}
token = requests.post("http://localhost:8000/auth/login", data=login_data).json()["access_token"]
headers = {"Authorization": f"Bearer {token}"}

def test_payload(count):
    payload = {
        "action": "delete_database",
        "record_count": count,
        "external": False,
        "classification": "Auto-Detect via AI Engine",
        "agent_id": "test_agent"
    }
    res = requests.post("http://localhost:8000/execute/", json=payload, headers=headers)
    if res.status_code != 200:
        print(f"Error {res.status_code} on execute!")
        sys.exit(1)
    return res.json()["result"]["decision"]

dec_499 = test_payload(499)
print(f"Record count 499 -> Decision: {dec_499}")

dec_500 = test_payload(500)
print(f"Record count 500 -> Decision: {dec_500}")

if dec_499 != "allow" and dec_499 != "log_and_allow":
    print("499 should be allowed!")
    sys.exit(1)

if dec_500 != "block":
    print("500 should be blocked!")
    sys.exit(1)

print("All tests passed perfectly!")
