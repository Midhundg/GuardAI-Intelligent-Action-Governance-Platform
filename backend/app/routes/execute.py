from uuid import uuid4

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.policy_engine import PolicyEngine
from app.dependencies import get_db
from app.models.audit import AuditLog
from app.schemas.action import (
    ActionRequest,
    ActionResponse,
    PolicyDecision,
)

router = APIRouter(
    prefix="/execute",
    tags=["Policy Execution"],
)

policy_engine = PolicyEngine()


@router.post("/", response_model=ActionResponse)
def execute_action(
    request: ActionRequest,
    db: Session = Depends(get_db),
):
    request_id = str(uuid4())

    # Evaluate policy
    result = policy_engine.evaluate(request.model_dump())

    # Save audit log
    audit = AuditLog(
        request_id=request_id,
        action=request.action,
        decision=result["decision"],
        reason=result["reason"],
    )

    db.add(audit)
    db.commit()

    return ActionResponse(
        request_id=request_id,
        request=request,
        result=PolicyDecision(
            decision=result["decision"],
            reason=result["reason"],
            matched_policy=result["matched_policy"],
            risk_score=result["risk_score"],
            risk_level=result["risk_level"],
            confidence=result["confidence"],
            explanation=result["explanation"],
            trace=result["trace"],
        ),
    )