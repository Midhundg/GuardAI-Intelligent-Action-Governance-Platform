from app.database import SessionLocal
from app.models.policy import Policy
from app.core.risk_engine import RiskEngine
from app.core.trace_engine import TraceEngine


class PolicyEngine:

    def __init__(self):
        self.risk_engine = RiskEngine()

    def evaluate(self, action_data: dict):

        db = SessionLocal()
        trace = TraceEngine()

        try:
            trace.add("Policy evaluation started.")

            policies = (
                db.query(Policy)
                .filter(Policy.enabled == True)
                .all()
            )

            trace.add(f"Loaded {len(policies)} active policies.")

            for policy in policies:

                trace.add(
                    f"Checking Policy #{policy.id}: {policy.name}"
                )

                # --------------------------------------------------
                # Match Action
                # --------------------------------------------------
                if action_data.get("action") != policy.action:
                    trace.add("Action does not match.")
                    continue

                trace.add("Action matched.")

                matched = False

                # --------------------------------------------------
                # Record Count
                # --------------------------------------------------
                if policy.condition_type == "record_count_gt":

                    threshold = int(policy.condition_value)

                    trace.add(
                        f"Evaluating record_count > {threshold}"
                    )

                    matched = (
                        action_data.get("record_count", 0)
                        > threshold
                    )

                # --------------------------------------------------
                # External Access
                # --------------------------------------------------
                elif policy.condition_type == "external":

                    trace.add(
                        "Evaluating external access."
                    )

                    matched = (
                        action_data.get("external", False)
                        is True
                    )

                # --------------------------------------------------
                # Classification
                # --------------------------------------------------
                elif policy.condition_type == "classification":

                    trace.add(
                        "Evaluating classification."
                    )

                    matched = (
                        action_data.get("classification")
                        == policy.condition_value
                    )

                # --------------------------------------------------
                # Policy Matched
                # --------------------------------------------------
                if matched:

                    trace.add(
                        f"Policy #{policy.id} matched."
                    )

                    trace.add(
                        "Calculating risk score."
                    )

                    risk = self.risk_engine.calculate(
                        action_data,
                        policy
                    )

                    trace.add(
                        f"Risk Score = {risk['risk_score']}"
                    )

                    trace.add(
                        f"Risk Level = {risk['risk_level']}"
                    )

                    trace.add(
                        f"Decision = {policy.decision.upper()}"
                    )

                    trace.add(
                        "Policy evaluation completed."
                    )

                    return {
                        "decision": policy.decision,
                        "reason": policy.description
                        or "Policy matched.",
                        "matched_policy": policy.id,
                        "trace": trace.get_trace(),
                        **risk,
                    }

                trace.add("Condition not satisfied.")

            # --------------------------------------------------
            # No Policy Matched
            # --------------------------------------------------

            trace.add("No policy matched.")
            trace.add("Decision = ALLOW")
            trace.add("Policy evaluation completed.")

            return {
                "decision": "allow",
                "reason": "No matching policy.",
                "matched_policy": None,
                "risk_score": 10,
                "risk_level": "LOW",
                "confidence": 1.0,
                "explanation": [
                    "No policy matched."
                ],
                "trace": trace.get_trace(),
            }

        finally:
            db.close()