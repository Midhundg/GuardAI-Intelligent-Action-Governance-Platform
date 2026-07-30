from sqlalchemy.orm import Session
from sqlalchemy import func, desc

from app.models.policy import Policy
from app.models.audit import AuditLog
from app.models.approval import ApprovalRequest


class AnalyticsService:

    @staticmethod
    def get_dashboard(db: Session):
        policies = db.query(Policy).filter(Policy.is_deleted == False).all()

        total = len(policies)
        enabled = sum(1 for p in policies if p.enabled)
        disabled = total - enabled

        allow = sum(1 for p in policies if p.decision.lower() == "allow")
        block = sum(1 for p in policies if p.decision.lower() == "block")
        high_risk = sum(1 for p in policies if p.severity.upper() in ["HIGH", "CRITICAL"])

        # Total Audit requests
        total_requests = db.query(func.count(AuditLog.id)).scalar() or 0
        total_blocked = db.query(func.count(AuditLog.id)).filter(AuditLog.decision == "block").scalar() or 0
        total_allowed = db.query(func.count(AuditLog.id)).filter(AuditLog.decision == "allow").scalar() or 0

        # Approval metrics
        from datetime import datetime, timezone
        now = datetime.now(timezone.utc)
        pending_items = db.query(ApprovalRequest).filter(ApprovalRequest.status == "PENDING").all()
        expired_count = 0
        for item in pending_items:
            if item.expires_at:
                exp = item.expires_at
                if exp.tzinfo is None:
                    exp = exp.replace(tzinfo=timezone.utc)
                if exp < now:
                    item.status = "EXPIRED"
                    expired_count += 1
        if expired_count > 0:
            db.commit()

        total_approvals = db.query(func.count(ApprovalRequest.id)).scalar() or 0
        approved_count = db.query(func.count(ApprovalRequest.id)).filter(ApprovalRequest.status == "APPROVED").scalar() or 0
        rejected_count = db.query(func.count(ApprovalRequest.id)).filter(ApprovalRequest.status == "REJECTED").scalar() or 0
        pending_count = db.query(func.count(ApprovalRequest.id)).filter(ApprovalRequest.status == "PENDING").scalar() or 0

        approval_success_rate = (
            round((approved_count / total_approvals) * 100, 2)
            if total_approvals > 0 else 100.0
        )

        # Average Latency
        avg_latency = db.query(func.avg(AuditLog.execution_time_ms)).scalar() or 12.5

        # Most Used Agent
        top_agent_row = (
            db.query(AuditLog.agent_id, func.count(AuditLog.id).label("cnt"))
            .filter(AuditLog.agent_id != None)
            .group_by(AuditLog.agent_id)
            .order_by(desc("cnt"))
            .first()
        )
        most_used_agent = top_agent_row[0] if top_agent_row else "DevOps Agent"

        # Most Used Policy
        top_policy_row = (
            db.query(AuditLog.policy_id, func.count(AuditLog.id).label("cnt"))
            .filter(AuditLog.policy_id != None)
            .group_by(AuditLog.policy_id)
            .order_by(desc("cnt"))
            .first()
        )
        most_used_policy_id = top_policy_row[0] if top_policy_row else None
        most_used_policy_name = "Default Guard Policy"
        if most_used_policy_id:
            pol = db.query(Policy).filter(Policy.id == most_used_policy_id).first()
            if pol:
                most_used_policy_name = pol.name

        # Governance Score calculation
        score = 100
        score -= disabled * 2
        score -= high_risk * 3
        score = max(score, 0)

        return {
            "total_policies": total,
            "enabled_policies": enabled,
            "disabled_policies": disabled,
            "allow_policies": allow,
            "block_policies": block,
            "high_risk_policies": high_risk,
            "overall_governance_score": score,

            # Advanced metrics
            "total_requests": total_requests,
            "blocked_actions": total_blocked,
            "allowed_actions": total_allowed,
            "total_approvals": total_approvals,
            "approved_count": approved_count,
            "rejected_count": rejected_count,
            "pending_approvals": pending_count,
            "approval_success_rate": approval_success_rate,
            "average_latency_ms": round(float(avg_latency), 2),
            "most_used_agent": most_used_agent,
            "most_used_policy": most_used_policy_name,
        }

    @staticmethod
    def get_daily_requests(db: Session):
        results = (
            db.query(
                func.date(AuditLog.created_at).label("day"),
                func.count(AuditLog.id).label("requests"),
            )
            .group_by("day")
            .order_by("day")
            .limit(30)
            .all()
        )
        return [
            {"date": str(day) if day else "Today", "requests": cnt}
            for day, cnt in results
        ]