import time
import logging
from uuid import uuid4
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

try:
    import structlog
    logger = structlog.get_logger()
except ImportError:
    logger = logging.getLogger("execute_router")

from app.core.policy_engine import PolicyEngine
from app.core.prompt_security import prompt_scanner
from app.core.llm_security import llm_security_service
from app.core.telemetry import REQUEST_COUNTER, POLICY_VIOLATION_COUNTER, APPROVAL_COUNTER
from app.dependencies import get_db, require_roles
from app.models.approval import ApprovalRequest
from app.models.audit import AuditLog
from app.models.cost_log import LLMCostLog
from app.models.prompt_scan import PromptScanLog
from app.models.user import User
from app.schemas.action import ActionRequest, ActionResponse, PolicyDecision
from app.tasks.audit_tasks import log_audit_event_task

router = APIRouter(
    prefix="/execute",
    tags=["Policy Execution"],
)

policy_engine = PolicyEngine()


@router.post("/", response_model=ActionResponse)
def execute_action(
    action_req: ActionRequest,
    req: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("USER", "EMPLOYEE", "MANAGER", "ADMIN", "AI_AGENT")),
):
    start_time = time.perf_counter()
    request_id = getattr(req.state, "request_id", str(uuid4()))
    correlation_id = getattr(req.state, "correlation_id", request_id)

    # 1. Prompt Security Scanning
    warnings = []
    security_scan_res = None
    if action_req.prompt:
        security_scan_res = prompt_scanner.scan(action_req.prompt)
        if security_scan_res["has_warnings"]:
            warnings = security_scan_res["warnings"]
            db_scan = PromptScanLog(
                request_id=request_id,
                user_id=current_user.id,
                has_warnings=True,
                detected_threats=str(security_scan_res["threats"]),
            )
            db.add(db_scan)

    # 2. Evaluate Policy & Calculate Risk
    result = policy_engine.evaluate(action_req.model_dump())

    # 3. AI Decision Natural Language Explainability
    ai_explanation = llm_security_service.generate_decision_explanation(
        action=action_req.action,
        decision=result["decision"],
        risk_score=result["risk_score"],
        risk_level=result["risk_level"],
        confidence=result["confidence"],
        matched_policy_name=result.get("matched_policy_name"),
        reason=result.get("reason"),
    )

    # 4. Token & Cost Logging
    prompt_len = len(action_req.prompt) if action_req.prompt else 20
    estimated_prompt_tokens = max(5, prompt_len // 4)
    estimated_completion_tokens = 50
    estimated_cost = llm_security_service.calculate_cost(
        provider="openai",
        model_name=action_req.model_name or "gpt-4o-mini",
        prompt_tokens=estimated_prompt_tokens,
        completion_tokens=estimated_completion_tokens,
    )

    cost_log = LLMCostLog(
        request_id=request_id,
        user_id=current_user.id,
        provider="openai",
        model_name=action_req.model_name or "gpt-4o-mini",
        prompt_tokens=estimated_prompt_tokens,
        completion_tokens=estimated_completion_tokens,
        total_tokens=estimated_prompt_tokens + estimated_completion_tokens,
        estimated_cost_usd=estimated_cost,
    )
    db.add(cost_log)

    # 5. Process Decision & Approval Workflow
    approval_request_id = None
    status = "COMPLETED"
    message = None

    if result.get("decision") == "block":
        status = "BLOCKED"
        message = f"Action blocked by policy rule: {result.get('reason')}"
        POLICY_VIOLATION_COUNTER.labels(
            policy_id=str(result.get("matched_policy") or "0"),
            action=action_req.action,
            severity=result["risk_level"],
        ).inc()
    elif result.get("decision") == "require_hitl":
        approval = ApprovalRequest(
            request_id=request_id,
            action=action_req.action,
            requested_by=current_user.id,
            status="PENDING",
            expires_at=datetime.now(timezone.utc) + timedelta(hours=24),
        )
        db.add(approval)
        db.flush()
        approval_request_id = approval.id
        status = "PENDING_APPROVAL"
        message = "High-risk action requires manager approval."
        APPROVAL_COUNTER.labels(status="PENDING").inc()

    exec_time_ms = round((time.perf_counter() - start_time) * 1000, 2)

    # 6. Audit Logging
    audit_data = {
        "request_id": request_id,
        "correlation_id": correlation_id,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "action": action_req.action,
        "request": f"{current_user.username}: {action_req.model_dump()}",
        "decision": result["decision"],
        "reason": result["reason"],
        "user_id": current_user.id,
        "agent_id": action_req.agent_id or getattr(req.state, "agent_id", "unknown"),
        "policy_id": result.get("matched_policy"),
        "risk_score": result["risk_score"],
        "risk_level": result["risk_level"],
        "execution_time_ms": exec_time_ms,
    }

    db_audit = AuditLog(**audit_data)
    db.add(db_audit)

    try:
        log_audit_event_task.apply_async(args=[request_id, action_req.model_dump(), result], expires=5)
    except Exception:
        pass

    db.commit()
    REQUEST_COUNTER.labels(endpoint="/execute/", status=status).inc()

    policy_decision = PolicyDecision(
        decision=result["decision"],
        reason=result["reason"],
        matched_policy=result.get("matched_policy"),
        matched_policy_name=result.get("matched_policy_name"),
        suggested_alternative=result.get("suggested_alternative"),
        risk_score=result["risk_score"],
        risk_level=result["risk_level"],
        confidence=result["confidence"],
        explanation=result["explanation"],
        factors_considered=result.get("factors_considered", []),
        why_risky=result.get("why_risky", []),
        recommended_mitigation=result.get("recommended_mitigation", []),
        trace=result["trace"],
        ai_explanation=ai_explanation,
        security_scan=security_scan_res,
    )

    return ActionResponse(
        request_id=request_id,
        correlation_id=correlation_id,
        status=status,
        approval_request_id=approval_request_id,
        message=message,
        request=action_req,
        result=policy_decision,
        warnings=warnings,
    )