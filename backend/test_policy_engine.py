import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.policy_engine import PolicyEngine

engine = PolicyEngine()

tests = [
    ({"action": "delete_database", "record_count": 150}, "block"),
    ({"action": "delete_database", "record_count": 5}, "allow"),
    ({"action": "send_email", "email_id": "hacker@gmail.com"}, "require_hitl"),
    ({"action": "send_email", "email_id": "john@company.com"}, "allow"),
    ({"action": "read_file", "path": "/data/confidential_report.pdf"}, "log_and_allow"),
]

print("\n--- Running PS-3.1 Backend Tests ---")
for payload, expected in tests:
    res = engine.evaluate(payload)
    actual = res["decision"]
    reason = res["reason"]
    print(f"Action: {payload['action']}")
    print(f"Payload: {payload}")
    print(f"Expected: {expected.upper()} | Actual: {actual.upper()}")
    print(f"Reason: {reason}")
    if expected == actual:
        print("✅ PASSED")
    else:
        print("❌ FAILED")
    print("-" * 50)
