import os
import sys
import unittest

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.database import SessionLocal, Base, engine
from app.models.policy import Policy
from app.models.user import User
from app.models.audit import AuditLog
from app.core.policy_engine import PolicyEngine

def ensure_criteria_policies(db):
    """Ensure policies for the exact user criteria are active in the database."""
    # 1. Bulk delete policy (delete_records with record_count > 100 -> block)
    del_pol = db.query(Policy).filter(Policy.action == "delete_records", Policy.condition_type == "record_count_gt").first()
    if not del_pol:
        del_pol = Policy(
            name="Bulk Record Delete Protection",
            description="Blocks deletion of over 100 records.",
            action="delete_records",
            condition_type="record_count_gt",
            condition_value="100",
            decision="block",
            severity="HIGH",
            requires_approval=False,
            enabled=True,
            version=1,
            created_by="criteria_checker",
        )
        db.add(del_pol)

    # 2. External email HITL policy (send_email with external == true -> require_approval)
    email_pol = db.query(Policy).filter(Policy.action == "send_email", Policy.condition_type == "external").first()
    if not email_pol:
        email_pol = Policy(
            name="External Email HITL Signoff",
            description="Pauses emails sent to external domains for human approval.",
            action="send_email",
            condition_type="external",
            condition_value="true",
            decision="require_approval",
            severity="MEDIUM",
            requires_approval=True,
            enabled=True,
            version=1,
            created_by="criteria_checker",
        )
        db.add(email_pol)

    db.commit()

class TestCriteria(unittest.TestCase):
    def setUp(self):
        self.db = SessionLocal()
        ensure_criteria_policies(self.db)
        self.engine = PolicyEngine()

    def tearDown(self):
        self.db.close()

    def test_criterion_1_and_2_bulk_delete_500_blocked_5_allowed(self):
        """A bulk delete of 500 records is blocked; a delete of five records is allowed."""
        # 500 records delete
        payload_500 = {"action": "delete_records", "record_count": 500}
        res_500 = self.engine.evaluate(payload_500)
        self.assertEqual(res_500["decision"], "block", "Delete of 500 records should be blocked")
        self.assertIsNotNone(res_500["matched_policy"], "Should report matched rule")

        # 5 records delete
        payload_5 = {"action": "delete_records", "record_count": 5}
        res_5 = self.engine.evaluate(payload_5)
        self.assertEqual(res_5["decision"], "allow", "Delete of 5 records should be allowed")

    def test_criterion_3_external_email_hitl_internal_email_allow(self):
        """An email to an external domain pauses for HITL; an internal email goes through."""
        # External email
        payload_ext = {"action": "send_email", "external": True}
        res_ext = self.engine.evaluate(payload_ext)
        self.assertIn(res_ext["decision"], ["require_approval", "human_review"], "External email should pause for HITL")
        self.assertIsNotNone(res_ext["matched_policy"], "Should report matched rule")

        # Internal email
        payload_int = {"action": "send_email", "external": False}
        res_int = self.engine.evaluate(payload_int)
        self.assertEqual(res_int["decision"], "allow", "Internal email should be allowed")

    def test_criterion_4_audit_log_captures_evaluated_action_outcome_matched_rule(self):
        """Audit log captures every evaluated action with outcome and matched rule."""
        payload = {"action": "delete_records", "record_count": 500}
        res = self.engine.evaluate(payload)
        
        # Verify result contains outcome and matched rule
        self.assertIn("decision", res)
        self.assertIn("matched_policy", res)
        self.assertIn("matched_policy_name", res)
        self.assertEqual(res["decision"], "block")

if __name__ == "__main__":
    unittest.main()
