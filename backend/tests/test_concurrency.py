import pytest
import concurrent.futures
from app.database import SessionLocal
from app.routes.execute import execute_action
from app.schemas.action import ActionRequest
from app.models.user import User
from unittest.mock import MagicMock

def test_concurrent_policy_execution():
    db = SessionLocal()
    mock_user = db.query(User).filter(User.username == "test_admin").first()
    if not mock_user:
        mock_user = User(id=1, username="test_admin", role="ADMIN")
    db.close()

    def run_execution(i):
        session = SessionLocal()
        try:
            req = MagicMock()
            req.state.request_id = f"req-concurrent-{i}"
            req.state.correlation_id = f"corr-concurrent-{i}"
            req.state.agent_id = "stress_agent"

            action_req = ActionRequest(
                action="delete_records",
                record_count=i * 10,
                external=False,
                prompt=f"Concurrent test execution iteration {i}"
            )
            res = execute_action(action_req=action_req, req=req, db=session, current_user=mock_user)
            return res.status
        finally:
            session.close()

    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(run_execution, i) for i in range(1, 21)]
        results = [f.result() for f in concurrent.futures.as_completed(futures)]

    assert len(results) == 20
    assert all(r in ("COMPLETED", "PENDING_APPROVAL", "BLOCKED") for r in results)
