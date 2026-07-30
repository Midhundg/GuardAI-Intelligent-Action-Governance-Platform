import sys
import logging
from app.core.simulation_engine import SimulationEngine

logging.basicConfig(level=logging.INFO)

engine = SimulationEngine()

scenarios = [
    {
        "name": "Delete 500 records -> BLOCK",
        "action_data": {"action": "delete_database", "record_count": 500},
        "expected_decision": "block"
    },
    {
        "name": "Delete 5 records -> ALLOW",
        "action_data": {"action": "delete_database", "record_count": 5},
        "expected_decision": "allow"
    },
    {
        "name": "Send email to external domain -> REQUIRE_HITL",
        "action_data": {"action": "send_email", "external": True},
        "expected_decision": "require_hitl"
    },
    {
        "name": "Send email to internal domain -> ALLOW",
        "action_data": {"action": "send_email", "external": False},
        "expected_decision": "allow"
    },
    {
        "name": "Read a file containing 'confidential' in its path -> LOG_AND_ALLOW",
        "action_data": {"action": "read_file", "path": "/path/to/confidential/file.txt"},
        "expected_decision": "log_and_allow"
    }
]

failed = False
for scenario in scenarios:
    print(f"Testing: {scenario['name']}")
    res = engine.simulate(scenario["action_data"])
    actual = res["decision"]
    if actual != scenario["expected_decision"]:
        print(f"  [FAIL] Expected {scenario['expected_decision']}, got {actual}")
        failed = True
    else:
        print(f"  [PASS] Got {actual}")

if failed:
    sys.exit(1)
print("All scenarios passed!")
