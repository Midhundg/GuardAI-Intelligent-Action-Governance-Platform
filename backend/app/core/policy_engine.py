from app.database import SessionLocal
from app.models.policy import Policy
from app.core.risk_engine import RiskEngine
from app.core.trace_engine import TraceEngine
from app.core.cache import cache


class PolicyEngine:

    def __init__(self):
        self.risk_engine = RiskEngine()

    def evaluate(self, action_data: dict):
        db = SessionLocal()
        trace = TraceEngine()

        try:
            trace.add("Policy evaluation started.")

            # Check cache for policy list
            cache_key = "active_policies"
            cached_policies = cache.get(cache_key)

            if cached_policies:
                trace.add("Loaded active policies from cache.")
                # We query DB for full objects to ensure SQLAlchemy mapping integrity
                policies = (
                    db.query(Policy)
                    .filter(Policy.enabled == True, Policy.is_deleted == False)
                    .all()
                )
            else:
                policies = (
                    db.query(Policy)
                    .filter(Policy.enabled == True, Policy.is_deleted == False)
                    .all()
                )
                cache.set(
                    cache_key,
                    [{"id": p.id, "name": p.name, "action": p.action} for p in policies],
                    ttl_seconds=60,
                )

            trace.add(f"Loaded {len(policies)} active policies.")

            for policy in policies:
                trace.add(f"Checking Policy #{policy.id}: {policy.name}")

                # -----------------------------
                # Match Action (Supports Synonyms)
                # -----------------------------
                req_action = str(action_data.get("action", "")).lower()
                pol_action = str(policy.action).lower()

                action_matched = (
                    req_action == pol_action
                    or (pol_action in ("delete_records", "delete_database") and req_action in ("delete_records", "delete_database"))
                    or (pol_action in ("read_file", "read_path") and req_action in ("read_file", "read_path"))
                )

                if not action_matched:
                    trace.add("Action does not match.")
                    continue

                trace.add("Action matched.")
                matched = False

                # -----------------------------
                # Record Count Condition
                # -----------------------------
                if policy.condition_type == "record_count_gt":
                    threshold = int(policy.condition_value)
                    trace.add(f"Evaluating record_count > {threshold}")
                    matched = int(action_data.get("record_count", 0)) > threshold

                # -----------------------------
                # External Access Condition
                # -----------------------------
                elif policy.condition_type == "external":
                    trace.add("Evaluating external access.")
                    matched = bool(action_data.get("external", False)) is True

                # -----------------------------
                # Classification Condition
                # -----------------------------
                elif policy.condition_type == "classification":
                    trace.add("Evaluating classification.")
                    req_class = str(action_data.get("classification", "")).lower()
                    prompt_text = str(action_data.get("prompt", "")).lower()
                    matched = (req_class == policy.condition_value.lower()) or (policy.condition_value.lower() in prompt_text)

                # -----------------------------
                # Policy Matched
                # -----------------------------
                if matched:
                    trace.add(f"Policy #{policy.id} matched.")
                    trace.add("Calculating risk score.")

                    risk = self.risk_engine.calculate(action_data, policy)

                    trace.add(f"Risk Score = {risk['risk_score']}")
                    trace.add(f"Risk Level = {risk['risk_level']}")
                    trace.add(f"Decision = {policy.decision.upper()}")
                    trace.add("Policy evaluation completed.")

                    suggested_alternative = "No alternative specified."
                    if policy.decision.lower() == "block":
                        if policy.condition_type == "record_count_gt":
                            suggested_alternative = f"Reduce record_count to {int(policy.condition_value)} or less, or submit request for bulk export approval."
                        elif policy.condition_type == "external":
                            suggested_alternative = "Use internal network endpoints or request an external proxy gateway exception."
                        elif policy.condition_type == "classification":
                            suggested_alternative = "De-classify or redact confidential fields before submitting prompt."

                    return {
                        "decision": policy.decision.lower(),
                        "reason": policy.description or f"Matched rule '{policy.name}'.",
                        "matched_policy": policy.id,
                        "matched_policy_name": policy.name,
                        "matched_policy_description": policy.description,
                        "suggested_alternative": suggested_alternative,
                        "trace": trace.get_trace(),
                        **risk,
                    }

                trace.add("Condition not satisfied.")

            # -----------------------------
            # No Policy Matched
            # -----------------------------
            trace.add("No policy matched.")
            trace.add("Calculating inherent risk.")

            risk = self.risk_engine.calculate(action_data)

            trace.add(f"Risk Score = {risk['risk_score']}")
            trace.add(f"Risk Level = {risk['risk_level']}")
            trace.add("Decision = ALLOW")
            trace.add("Policy evaluation completed.")

            return {
                "decision": "allow",
                "reason": "No matching policy.",
                "matched_policy": None,
                "matched_policy_name": None,
                "matched_policy_description": None,
                "suggested_alternative": None,
                "trace": trace.get_trace(),
                **risk,
            }

        finally:
            db.close()