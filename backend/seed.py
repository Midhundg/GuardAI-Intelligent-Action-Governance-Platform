import sys
import os
from datetime import datetime, timedelta, timezone

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.database import SessionLocal, Base, engine
from app.models.user import User
from app.models.policy import Policy
from app.models.approval import ApprovalRequest
from app.models.audit import AuditLog
from app.models.cost_log import LLMCostLog
from app.auth.passwords import hash_password

def seed_database():
    """Seed the database with sample users, policies, approvals, and audit logs."""
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    try:
        print("🌱 Seeding database...")

        # 1. Users
        users_data = [
            {"username": "admin", "email": "admin@guardai.enterprise", "role": "ADMIN", "department": "Security & Risk"},
            {"username": "manager_jane", "email": "jane@guardai.enterprise", "role": "MANAGER", "department": "DevOps Lead"},
            {"username": "dev_alex", "email": "alex@guardai.enterprise", "role": "EMPLOYEE", "department": "Engineering"},
            {"username": "auditor_bob", "email": "bob@guardai.enterprise", "role": "AUDITOR", "department": "Compliance"},
            {"username": "coding_agent", "email": "agent.coding@guardai.enterprise", "role": "AI_AGENT", "department": "Autonomous AI"},
        ]

        created_users = {}
        for u in users_data:
            existing = db.query(User).filter(User.username == u["username"]).first()
            if not existing:
                usr = User(
                    username=u["username"],
                    email=u["email"],
                    password_hash=hash_password("Password123!"),
                    role=u["role"],
                    department=u["department"],
                    is_active=True,
                )
                db.add(usr)
                db.flush()
                created_users[u["username"]] = usr
            else:
                created_users[u["username"]] = existing

        # 2. Enterprise Policies
        policies_data = [
            {
                "name": "External Email HITL Signoff",
                "description": "Pauses emails sent to external domains for human approval.",
                "action": "send_email",
                "condition_type": "external",
                "condition_value": "true",
                "decision": "require_approval",
                "severity": "MEDIUM",
                "requires_approval": True,
            },
            {
                "name": "Block Database Purge Operations",
                "description": "Prevents AI agents from carrying out destructive database drops or mass deletes without authorization.",
                "action": "delete_database",
                "condition_type": "record_count_gt",
                "condition_value": "0",
                "decision": "block",
                "severity": "CRITICAL",
                "requires_approval": True,
            },
            {
                "name": "Confidential Classification Protection",
                "description": "Requires explicit manager signoff when accessing confidential internal files.",
                "action": "read_file",
                "condition_type": "classification",
                "condition_value": "confidential",
                "decision": "block",
                "severity": "HIGH",
                "requires_approval": True,
            },
        ]

        for p in policies_data:
            existing_p = db.query(Policy).filter(Policy.name == p["name"]).first()
            if not existing_p:
                pol = Policy(
                    name=p["name"],
                    description=p["description"],
                    action=p["action"],
                    condition_type=p["condition_type"],
                    condition_value=p["condition_value"],
                    decision=p["decision"],
                    severity=p["severity"],
                    requires_approval=p["requires_approval"],
                    enabled=True,
                    version=1,
                    created_by="system_seed",
                )
                db.add(pol)

        db.flush()

        # REMOVE ANY EXTRANEOUS POLICIES THAT MIGHT BE LEFTOVER IN A PERSISTENT DB
        db.query(Policy).filter(Policy.action.notin_(["delete_database", "read_file", "send_email"])).delete(synchronize_session=False)
        db.flush()

        # 3. Seed Sample Approvals
        dev_user = created_users.get("dev_alex")
        mgr_user = created_users.get("manager_jane")
        if dev_user and mgr_user:
            sample_approvals = [
                {
                    "request_id": "req-seed-001",
                    "action": "deploy_prod",
                    "requested_by": dev_user.id,
                    "status": "PENDING",
                    "expires_at": datetime.now(timezone.utc) + timedelta(hours=18),
                },
                {
                    "request_id": "req-seed-002",
                    "action": "export_records",
                    "requested_by": dev_user.id,
                    "status": "APPROVED",
                    "manager_id": mgr_user.id,
                    "decision_reason": "Verified bulk export authorization for Q3 audit report.",
                    "time_taken_seconds": 320,
                    "decided_at": datetime.now(timezone.utc) - timedelta(hours=2),
                },
            ]
            for sa in sample_approvals:
                if not db.query(ApprovalRequest).filter(ApprovalRequest.request_id == sa["request_id"]).first():
                    appr = ApprovalRequest(**sa)
                    db.add(appr)

        # 4. Seed Audit Logs & Cost Metrics
        if dev_user:
            logs = [
                AuditLog(
                    request_id="req-seed-101",
                    timestamp=datetime.now(timezone.utc).isoformat(),
                    action="delete_database",
                    request=f"dev_alex: {{'action': 'delete_database', 'record_count': 500}}",
                    decision="block",
                    reason="Destructive database operation detected.",
                    user_id=dev_user.id,
                    agent_id="devops_agent",
                    risk_score=95,
                    risk_level="CRITICAL",
                    execution_time_ms=14.2,
                ),
                AuditLog(
                    request_id="req-seed-102",
                    timestamp=datetime.now(timezone.utc).isoformat(),
                    action="read_file",
                    request=f"dev_alex: {{'action': 'read_file', 'classification': 'public'}}",
                    decision="allow",
                    reason="No matching policy.",
                    user_id=dev_user.id,
                    agent_id="coding_agent",
                    risk_score=10,
                    risk_level="LOW",
                    execution_time_ms=4.8,
                ),
            ]
            for l in logs:
                if not db.query(AuditLog).filter(AuditLog.request_id == l.request_id).first():
                    db.add(l)

            # Cost log
            cost = LLMCostLog(
                request_id="req-seed-101",
                user_id=dev_user.id,
                provider="openai",
                model_name="gpt-4o-mini",
                prompt_tokens=450,
                completion_tokens=120,
                total_tokens=570,
                estimated_cost_usd=0.00013,
            )
            db.add(cost)

        db.commit()
        print("✅ Database seeding completed successfully!")
    except Exception as e:
        db.rollback()
        print(f"❌ Seeding error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    seed_database()
