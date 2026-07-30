class RiskEngine:

    def calculate(self, action_data, policy):

        score = 0
        explanation = []

        # High-risk action
        if action_data.get("action") == "delete_database":
            score += 50
            explanation.append(
                "Destructive database operation detected."
            )

        # Bulk operation
        record_count = action_data.get("record_count", 0)

        if record_count > 100:
            score += 40
            explanation.append(
                f"Bulk operation detected ({record_count} records)."
            )

        # Policy match
        score += 10
        explanation.append(
            f"Matched policy #{policy.id}."
        )

        score = min(score, 100)

        if score >= 90:
            level = "CRITICAL"
        elif score >= 70:
            level = "HIGH"
        elif score >= 40:
            level = "MEDIUM"
        else:
            level = "LOW"

        return {
            "risk_score": score,
            "risk_level": level,
            "confidence": 0.98,
            "explanation": explanation,
        }