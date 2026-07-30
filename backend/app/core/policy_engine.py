"""
PolicyEngine — PS-3.1 Action Guardrail
Pre-execution evaluator that checks every tool call against the declarative
YAML policy ruleset (policies.yaml) before dispatching.

Decision outcomes:
  block         - Reject the call entirely
  require_hitl  - Pause for human-in-the-loop review
  log_and_allow - Execute but create an audit record
"""

import os
import yaml
from app.database import SessionLocal
from app.models.policy import Policy
from app.core.risk_engine import RiskEngine
from app.core.trace_engine import TraceEngine
from app.core.cache import cache

# Path to the declarative YAML policy ruleset
YAML_POLICY_FILE = os.path.join(os.path.dirname(__file__), "policies.yaml")


def _load_yaml_policies() -> list[dict]:
    """Load policy rules from the declarative YAML file."""
    try:
        with open(YAML_POLICY_FILE, "r") as f:
            data = yaml.safe_load(f)
        return data.get("rules", [])
    except FileNotFoundError:
        return []
    except Exception:
        return []


class YamlPolicyRule:
    """Lightweight wrapper to provide uniform interface for YAML-sourced rules."""

    def __init__(self, rule: dict, index: int):
        self.id = rule.get("id", f"yaml-{index}")
        self.name = rule.get("name", "Unnamed YAML Rule")
        self.description = rule.get("description", "")
        self.action = rule.get("action", "")
        self.synonyms = [s.lower() for s in rule.get("synonyms", [])]
        self.decision = rule.get("decision", "allow")
        self.severity = rule.get("severity", "LOW")
        self.requires_approval = rule.get("requires_approval", False)
        self.tags = rule.get("tags", [])
        self.source = "yaml"

        condition = rule.get("condition", {})
        self.condition_type = condition.get("type", "")
        raw_value = condition.get("value", "")
        self.condition_value = str(raw_value)

    def matches_action(self, req_action: str) -> bool:
        """Check if the requested action matches this rule (including synonyms)."""
        req = req_action.lower()
        pol = self.action.lower()
        return req == pol or req in self.synonyms or pol in [req]


class PolicyEngine:

    def __init__(self):
        self.risk_engine = RiskEngine()

    def _get_policies(self, db, trace):
        """Load policies from YAML first, then augment with DB policies."""

        # 1. Load from YAML (primary source per PS-3.1 spec)
        yaml_rules_raw = _load_yaml_policies()
        yaml_rules = [YamlPolicyRule(r, i) for i, r in enumerate(yaml_rules_raw)]
        trace.add(f"Loaded {len(yaml_rules)} rules from YAML policy file.")

        # 2. Load DB policies (user-defined via dashboard)
        cache_key = "active_policies"
        cached_policies = cache.get(cache_key)

        if not cached_policies:
            db_policies = (
                db.query(Policy)
                .filter(Policy.enabled == True, Policy.is_deleted == False)
                .all()
            )
            cache.set(
                cache_key,
                [{"id": p.id, "name": p.name, "action": p.action} for p in db_policies],
                ttl_seconds=60,
            )
        else:
            db_policies = (
                db.query(Policy)
                .filter(Policy.enabled == True, Policy.is_deleted == False)
                .all()
            )
        trace.add(f"Loaded {len(db_policies)} rules from database.")

        return yaml_rules, db_policies

    def evaluate(self, action_data: dict):
        db = SessionLocal()
        trace = TraceEngine()

        try:
            trace.add("Policy evaluation started (PS-3.1 Action Guardrail).")
            req_action = str(action_data.get("action", "")).lower()
            record_count = int(action_data.get("record_count", 0))
            is_external = bool(action_data.get("external", False))
            classification = str(action_data.get("classification", "")).lower()
            prompt_text = str(action_data.get("prompt", "")).lower()
            path = str(action_data.get("path", "")).lower()
            email_id = str(action_data.get("email_id", "")).lower()

            yaml_rules, db_policies = self._get_policies(db, trace)

            # ---------------------------------------------------------------
            # Phase 1: Evaluate YAML rules first (declarative policy source)
            # ---------------------------------------------------------------
            trace.add("--- Phase 1: Evaluating YAML policy rules ---")
            for rule in yaml_rules:
                trace.add(f"Checking YAML Rule [{rule.id}]: {rule.name}")

                if not rule.matches_action(req_action):
                    trace.add(f"  Action '{req_action}' does not match rule action '{rule.action}'.")
                    continue

                trace.add(f"  Action '{req_action}' matched rule '{rule.name}'.")
                matched = self._evaluate_condition(rule, record_count, is_external, classification, prompt_text, path, email_id, trace)

                if matched:
                    trace.add(f"  Condition matched. Decision = {rule.decision.upper()}")
                    risk = self.risk_engine.calculate(action_data, None)
                    suggested = self._suggest_alternative(rule.decision, rule.condition_type, rule.condition_value)

                    return {
                        "decision": rule.decision.lower(),
                        "reason": rule.description.strip() if rule.description else f"Matched YAML rule '{rule.name}'.",
                        "matched_policy": rule.id,
                        "matched_policy_name": rule.name,
                        "matched_policy_description": rule.description.strip(),
                        "suggested_alternative": suggested,
                        "policy_source": "yaml",
                        "trace": trace.get_trace(),
                        **risk,
                    }

                trace.add(f"  Condition not satisfied for rule '{rule.name}'.")

            # ---------------------------------------------------------------
            # Phase 2: Evaluate DB policies (user-defined rules from dashboard)
            # ---------------------------------------------------------------
            trace.add("--- Phase 2: Evaluating database policy rules (DISABLED PER PS-3.1) ---")
            # Disabled DB rules to ensure YAML is the primary source of truth
            """
            for policy in db_policies:
                trace.add(f"Checking DB Policy #{policy.id}: {policy.name}")

                pol_action = str(policy.action).lower()
                action_matched = (
                    req_action == pol_action
                    or (pol_action in ("delete_records", "delete_database") and req_action in ("delete_records", "delete_database"))
                    or (pol_action in ("read_file", "read_path") and req_action in ("read_file", "read_path"))
                )

                if not action_matched:
                    trace.add(f"  Action does not match policy action '{policy.action}'.")
                    continue

                trace.add("  Action matched.")
                matched = self._evaluate_db_condition(policy, record_count, is_external, classification, prompt_text, trace)

                if matched:
                    trace.add(f"  Condition matched. Decision = {policy.decision.upper()}")
                    risk = self.risk_engine.calculate(action_data, policy)
                    suggested = self._suggest_alternative(policy.decision, policy.condition_type, policy.condition_value)

                    return {
                        "decision": policy.decision.lower(),
                        "reason": policy.description or f"Matched DB rule '{policy.name}'.",
                        "matched_policy": policy.id,
                        "matched_policy_name": policy.name,
                        "matched_policy_description": policy.description,
                        "suggested_alternative": suggested,
                        "policy_source": "database",
                        "trace": trace.get_trace(),
                        **self.risk_engine.calculate(action_data, policy),
                    }

                trace.add("  Condition not satisfied.")
            """

            # ---------------------------------------------------------------
            # No Policy Matched — Default Allow with risk assessment
            # ---------------------------------------------------------------
            trace.add("No policy matched. Calculating inherent risk score.")
            risk = self.risk_engine.calculate(action_data)
            trace.add(f"Risk Score = {risk['risk_score']} | Level = {risk['risk_level']}")
            trace.add("Decision = ALLOW")

            return {
                "decision": "allow",
                "reason": "No matching policy rule found. Action permitted by default.",
                "matched_policy": None,
                "matched_policy_name": None,
                "matched_policy_description": None,
                "suggested_alternative": None,
                "policy_source": "none",
                "trace": trace.get_trace(),
                **risk,
            }

        finally:
            db.close()

    def _evaluate_condition(self, rule: YamlPolicyRule, record_count, is_external, classification, prompt_text, path, email_id, trace) -> bool:
        """Evaluate a YAML rule's condition against action data."""
        ctype = rule.condition_type
        cvalue = rule.condition_value

        if ctype == "record_count_gt":
            threshold = int(cvalue) if cvalue.isdigit() else 0
            result = record_count > threshold
            trace.add(f"  Condition: record_count ({record_count}) > {threshold} → {result}")
            return result

        elif ctype == "external":
            result = is_external is True
            trace.add(f"  Condition: external ({is_external}) = true → {result}")
            return result

        elif ctype == "classification":
            result = (classification == cvalue.lower()) or (cvalue.lower() in prompt_text)
            trace.add(f"  Condition: classification '{classification}' matches '{cvalue}' → {result}")
            return result

        elif ctype == "prompt_contains":
            result = cvalue.lower() in prompt_text
            trace.add(f"  Condition: prompt contains '{cvalue}' → {result}")
            return result

        elif ctype == "action_is":
            # Always matches (already filtered by action match above)
            trace.add(f"  Condition: action_is (always matched at action level) → True")
            return True

        elif ctype == "path_contains":
            result = cvalue.lower() in path
            trace.add(f"  Condition: path contains '{cvalue}' → {result}")
            return result
            
        elif ctype == "email_domain_not_contains":
            # If the domain is missing from the email address, it evaluates to True (to trigger the rule)
            result = bool(email_id) and cvalue.lower() not in email_id
            trace.add(f"  Condition: email_id '{email_id}' does not contain '{cvalue}' → {result}")
            return result

        trace.add(f"  Unknown condition type '{ctype}' — skipping.")
        return False

    def _evaluate_db_condition(self, policy, record_count, is_external, classification, prompt_text, trace) -> bool:
        """Evaluate a DB policy's condition."""
        if policy.condition_type == "record_count_gt":
            threshold = int(policy.condition_value)
            return record_count > threshold

        elif policy.condition_type == "external":
            return is_external is True

        elif policy.condition_type == "classification":
            return (classification == policy.condition_value.lower()) or (policy.condition_value.lower() in prompt_text)

        return False

    def _suggest_alternative(self, decision: str, condition_type: str, condition_value: str) -> str:
        """Generate a helpful alternative suggestion based on the decision and condition."""
        if decision.lower() == "block":
            if condition_type == "record_count_gt":
                return f"Reduce record_count to {condition_value} or fewer, or submit a bulk operation approval request."
            elif condition_type == "external":
                return "Use internal network endpoints or request an external proxy gateway exception."
            elif condition_type == "classification":
                return "De-classify or redact confidential fields before submitting the request."
            return "Review the action and submit a change management request for approval."

        elif decision.lower() == "require_hitl":
            return "This action is pending human review. A manager will be notified to approve or reject."

        elif decision.lower() == "log_and_allow":
            return "Action will proceed. An audit record has been created for compliance tracking."

        return "No alternative specified."