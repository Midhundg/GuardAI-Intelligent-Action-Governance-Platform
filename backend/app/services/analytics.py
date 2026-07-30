from sqlalchemy.orm import Session

from app.models.policy import Policy


class AnalyticsService:

    @staticmethod
    def get_dashboard(db: Session):
        policies = db.query(Policy).all()

        total = len(policies)

        enabled = sum(1 for p in policies if p.enabled)
        disabled = total - enabled

        allow = sum(
            1 for p in policies
            if p.decision.lower() == "allow"
        )

        block = sum(
            1 for p in policies
            if p.decision.lower() == "block"
        )

        high_risk = sum(
            1
            for p in policies
            if p.severity.upper() in ["HIGH", "CRITICAL"]
        )

        # Governance Score (simple scoring model)
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
        }