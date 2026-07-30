from typing import Dict, Any


class LLMSecurityService:
    """LLM cost calculation, decision explanation, and fallback routing helper."""

    # Cost per 1k tokens in USD
    MODEL_PRICING = {
        "gpt-4o": {"prompt": 0.005, "completion": 0.015},
        "gpt-4o-mini": {"prompt": 0.00015, "completion": 0.0006},
        "claude-3-5-sonnet": {"prompt": 0.003, "completion": 0.015},
        "claude-3-haiku": {"prompt": 0.00025, "completion": 0.00125},
        "bedrock-llama3": {"prompt": 0.0002, "completion": 0.0008},
    }

    @classmethod
    def calculate_cost(
        cls, provider: str, model_name: str, prompt_tokens: int, completion_tokens: int
    ) -> float:
        """Calculate estimated cost in USD based on provider and token counts."""
        pricing = cls.MODEL_PRICING.get(
            model_name.lower(), {"prompt": 0.002, "completion": 0.006}
        )
        prompt_cost = (prompt_tokens / 1000.0) * pricing["prompt"]
        completion_cost = (completion_tokens / 1000.0) * pricing["completion"]
        return round(prompt_cost + completion_cost, 6)

    @classmethod
    def generate_decision_explanation(
        cls,
        action: str,
        decision: str,
        risk_score: int,
        risk_level: str,
        confidence: float,
        matched_policy_name: str | None = None,
        reason: str | None = None,
    ) -> Dict[str, Any]:
        """Generate human-readable natural language AI decision explainability payload."""
        dec_upper = decision.upper()
        if dec_upper == "ALLOW":
            summary = f"The requested action '{action}' was ALLOWED because it complies with enterprise policy boundaries."
            detailed_why = f"Action evaluation yielded a risk score of {risk_score}/100 ({risk_level}). No blocking policies were violated."
        elif dec_upper == "BLOCK":
            summary = f"The requested action '{action}' was BLOCKED to prevent risk exposure."
            detailed_why = f"Action triggered security policy '{matched_policy_name or 'Default Risk Guard'}' with risk score {risk_score}/100 ({risk_level}). Reason: {reason or 'Exceeds allowable enterprise risk threshold'}."
        else:
            summary = f"The requested action '{action}' requires HUMAN-IN-THE-LOOP MANAGER APPROVAL."
            detailed_why = f"Action risk level is {risk_level} (Score: {risk_score}/100). Manager sign-off is mandatory before execution."

        return {
            "natural_language_explanation": summary,
            "why_decision_was_made": detailed_why,
            "relevant_policies": [matched_policy_name] if matched_policy_name else [],
            "confidence_score": confidence,
            "risk_summary": {
                "score": risk_score,
                "level": risk_level,
            },
        }

    @classmethod
    def resolve_llm_fallback(cls, preferred_provider: str = "openai") -> Dict[str, str]:
        """Demonstrate fallback routing architecture: OpenAI -> Anthropic -> AWS Bedrock -> Local Model."""
        providers = [
            {"provider": "openai", "model": "gpt-4o-mini", "status": "active"},
            {"provider": "anthropic", "model": "claude-3-haiku", "status": "standby"},
            {"provider": "bedrock", "model": "bedrock-llama3", "status": "standby"},
            {"provider": "local", "model": "ollama-llama3", "status": "fallback"},
        ]
        return {
            "active_provider": preferred_provider,
            "fallback_chain": providers,
            "circuit_breaker_status": "CLOSED",
        }


llm_security_service = LLMSecurityService()
