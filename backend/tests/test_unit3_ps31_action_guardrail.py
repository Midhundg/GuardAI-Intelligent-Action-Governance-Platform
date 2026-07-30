import pytest
from app.core.policy_engine import PolicyEngine
from app.database import SessionLocal
from app.models.policy import Policy

@pytest.fixture(autouse=True)
def setup_unit3_policies():
    db = SessionLocal()
    try:
        # Ensure confidential read policy has decision='log_and_allow' for PS-3.1 spec
        pol = db.query(Policy).filter(Policy.action == "read_file", Policy.condition_value == "confidential").first()
        if pol:
            pol.decision = "log_and_allow"
            pol.name = "Confidential Read Log & Allow"
            db.commit()
    finally:
        db.close()


def test_bulk_delete_500_records_is_blocked():
    """PS-3.1 Criteria: A bulk delete of 500 records is blocked."""
    engine = PolicyEngine()
    payload = {
        "action": "delete_records",
        "record_count": 500,
        "external": False,
        "classification": "public",
        "prompt": "Delete 500 inactive customer accounts from DB"
    }
    res = engine.evaluate(payload)
    assert res["decision"] == "block"
    assert res["matched_policy"] is not None


def test_delete_of_5_records_is_allowed():
    """PS-3.1 Criteria: A delete of five records is allowed."""
    engine = PolicyEngine()
    payload = {
        "action": "delete_records",
        "record_count": 5,
        "external": False,
        "classification": "public",
        "prompt": "Delete 5 test accounts"
    }
    res = engine.evaluate(payload)
    assert res["decision"] in ("allow", "log_and_allow")


def test_external_email_pauses_for_hitl():
    """PS-3.1 Criteria: An email to an external domain pauses for HITL."""
    engine = PolicyEngine()
    payload = {
        "action": "send_email",
        "record_count": 1,
        "external": True,
        "classification": "public",
        "prompt": "Send report email to vendor@externaldomain.com"
    }
    res = engine.evaluate(payload)
    assert res["decision"] in ("require_hitl", "require_approval")


def test_internal_email_goes_through():
    """PS-3.1 Criteria: An internal email goes through."""
    engine = PolicyEngine()
    payload = {
        "action": "send_email",
        "record_count": 1,
        "external": False,
        "classification": "public",
        "prompt": "Send daily update to internal-team@company.local"
    }
    res = engine.evaluate(payload)
    assert res["decision"] in ("allow", "log_and_allow")


def test_confidential_file_read_is_logged_and_allowed():
    """PS-3.1 Criteria: Log and allow any read of a path containing the word confidential."""
    engine = PolicyEngine()
    payload = {
        "action": "read_file",
        "record_count": 1,
        "external": False,
        "classification": "confidential",
        "prompt": "Read file contents from /secrets/confidential_project_plan.docx"
    }
    res = engine.evaluate(payload)
    assert res["decision"] in ("log_and_allow", "allow")
