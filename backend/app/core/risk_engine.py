class RiskEngine:

    def calculate(self, action_data: dict, policy=None):
        score = 0
        explanation = []
        factors_considered = []
        why_risky = []
        recommended_mitigation = []

        action_name = action_data.get("action", "")
        record_count = action_data.get("record_count", 0)
        is_external = action_data.get("external", False)
        classification = str(action_data.get("classification", "")).lower()

        # -----------------------------
        # 1. Action Risk Factor
        # -----------------------------
        factors_considered.append(f"Action Type: {action_name}")
        if action_name in ("delete_database", "drop_table", "purge_data"):
            score += 50
            explanation.append("Destructive database operation detected.")
            why_risky.append("Irreversible data deletion on storage systems.")
            recommended_mitigation.append("Require Multi-Factor Manager Approval before execution.")
        elif action_name in ("deploy_prod", "shell_execution", "sudo_run"):
            score += 45
            explanation.append("High-privilege system command requested.")
            why_risky.append("Execution could modify production infrastructure.")
            recommended_mitigation.append("Verify change management ticket and restrict shell permissions.")

        # -----------------------------
        # 2. Bulk Operation Risk Factor
        # -----------------------------
        factors_considered.append(f"Record Count: {record_count}")
        if record_count > 1000:
            score += 50
            explanation.append(f"Massive data operation ({record_count} records).")
            why_risky.append("Exceeds bulk export/update threshold limit.")
            recommended_mitigation.append("Batch process in smaller chunks under 100 records.")
        elif record_count > 100:
            score += 40
            explanation.append(f"Bulk operation detected ({record_count} records).")
            why_risky.append("Affects a significant number of data entities.")
            recommended_mitigation.append("Review records list and monitor rate limits.")

        # -----------------------------
        # 3. External Access Risk Factor
        # -----------------------------
        factors_considered.append(f"External Connection: {is_external}")
        if is_external:
            score += 20
            explanation.append("External system access detected.")
            why_risky.append("Data leaving internal network boundary.")
            recommended_mitigation.append("Enforce TLS encryption and audit destination domain IP.")

        # -----------------------------
        # 4. Data Sensitivity Risk Factor
        # -----------------------------
        factors_considered.append(f"Data Classification: {classification or 'unclassified'}")
        if classification in ("confidential", "restricted", "pii", "secret"):
            score += 20
            explanation.append("Confidential data involved.")
            why_risky.append("Potential data breach or compliance violation (GDPR/HIPAA).")
            recommended_mitigation.append("Apply PII masking and audit access token permissions.")

        # -----------------------------
        # 5. Policy Match Bonus Factor
        # -----------------------------
        if policy is not None:
            score += 10
            explanation.append(f"Matched policy #{policy.id}.")
            factors_considered.append(f"Policy Rule #{policy.id} ({policy.name})")

        score = min(score, 100)

        # Risk Level Classification
        if score >= 90:
            level = "CRITICAL"
        elif score >= 70:
            level = "HIGH"
        elif score >= 40:
            level = "MEDIUM"
        else:
            level = "LOW"

        if not why_risky:
            why_risky.append("Low operational impact action within standard boundaries.")
        if not recommended_mitigation:
            recommended_mitigation.append("Standard automated audit logging.")

        confidence = min(0.75 + (score / 100) * 0.25, 1.0)

        return {
            "risk_score": score,
            "risk_level": level,
            "confidence": round(confidence, 2),
            "explanation": explanation,
            "factors_considered": factors_considered,
            "why_risky": why_risky,
            "recommended_mitigation": recommended_mitigation,
        }