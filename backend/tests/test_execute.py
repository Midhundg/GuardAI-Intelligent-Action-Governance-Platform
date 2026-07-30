import unittest
from unittest.mock import MagicMock
from app.routes.execute import execute_action
from app.schemas.action import ActionRequest
from app.database import SessionLocal
from app.models.user import User


class TestExecution(unittest.TestCase):
    def setUp(self):
        self.db = SessionLocal()
        self.mock_user = self.db.query(User).filter(User.username == "admin").first()
        if not self.mock_user:
            self.mock_user = User(id=1, username="admin", role="ADMIN")

        self.mock_req = MagicMock()
        self.mock_req.state.request_id = "req-test-123"
        self.mock_req.state.correlation_id = "corr-test-123"
        self.mock_req.state.agent_id = "test_agent"

    def tearDown(self):
        self.db.close()

    def test_execute_allowed_action(self):
        action_req = ActionRequest(
            action="read_file",
            record_count=5,
            external=False,
            classification="public",
            prompt="Read public announcement"
        )
        res = execute_action(action_req=action_req, req=self.mock_req, db=self.db, current_user=self.mock_user)
        self.assertEqual(res.result.decision, "allow")
        self.assertIsNotNone(res.result.ai_explanation)

    def test_execute_high_risk_action(self):
        action_req = ActionRequest(
            action="delete_database",
            record_count=500,
            external=True,
            prompt="Delete outdated database"
        )
        res = execute_action(action_req=action_req, req=self.mock_req, db=self.db, current_user=self.mock_user)
        self.assertIn(res.result.risk_level, ("HIGH", "CRITICAL"))
        self.assertIn(res.status, ("PENDING_APPROVAL", "BLOCKED"))


if __name__ == "__main__":
    unittest.main()
