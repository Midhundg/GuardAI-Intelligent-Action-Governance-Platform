from sqlalchemy.orm import Session

from app.models.policy import Policy


class RecommendationEngine:

    @staticmethod
    def generate(db: Session):
        policies = db.query(Policy).all()

        recommendations = []

        for i in range(len(policies)):
            for j in range(i + 1, len(policies)):
                p1 = policies[i]
                p2 = policies[j]

                if (
                    p1.action == p2.action
                    and p1.condition_type == p2.condition_type
                    and p1.condition_value == p2.condition_value
                    and p1.decision != p2.decision
                ):
                    recommendations.append(
                        {
                            "conflict": f"{p1.name} ↔ {p2.name}",
                            "risk": "HIGH",
                            "recommendations": [
                                f"Disable '{p2.name}'",
                                "Increase the condition threshold",
                                "Require manager approval",
                                "Review governance policy consistency"
                            ]
                        }
                    )

        if not recommendations:
            recommendations.append(
                {
                    "status": "Healthy",
                    "message": "No policy conflicts detected.",
                    "recommendations": [
                        "Continue monitoring policies regularly."
                    ]
                }
            )

        return recommendations