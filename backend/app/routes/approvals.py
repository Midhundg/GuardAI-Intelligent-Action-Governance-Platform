import logging
from datetime import datetime, timezone
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

try:
    import structlog
    logger = structlog.get_logger()
except ImportError:
    logger = logging.getLogger("approvals_router")

from app.core.telemetry import APPROVAL_COUNTER
from app.dependencies import get_db, require_roles
from app.models.approval import ApprovalRequest
from app.models.user import User
from app.schemas.approval import ApprovalRequestResponse, ApprovalDecision

router = APIRouter(
    prefix="/approvals",
    tags=["Approval Workflows"],
)


@router.get("/", response_model=List[ApprovalRequestResponse])
def list_approvals(
    status_filter: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("MANAGER", "ADMIN", "AUDITOR")),
):
    query = db.query(ApprovalRequest)
    now = datetime.now(timezone.utc)
    expired_items = (
        query.filter(
            ApprovalRequest.status == "PENDING",
            ApprovalRequest.expires_at != None,
            ApprovalRequest.expires_at < now,
        ).all()
    )
    for exp in expired_items:
        exp.status = "EXPIRED"
        exp.decision_reason = "Automatically expired by SLA timer."
    if expired_items:
        db.commit()

    if status_filter:
        query = query.filter(ApprovalRequest.status == status_filter.upper())

    return query.order_by(ApprovalRequest.created_at.desc()).all()


@router.get("/pending", response_model=List[ApprovalRequestResponse])
def list_pending_approvals(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("MANAGER", "ADMIN")),
):
    now = datetime.now(timezone.utc)
    pending_items = db.query(ApprovalRequest).filter(ApprovalRequest.status == "PENDING").all()
    expired = []
    active_pending = []
    for item in pending_items:
        if item.expires_at:
            exp = item.expires_at
            if exp.tzinfo is None:
                exp = exp.replace(tzinfo=timezone.utc)
            if exp < now:
                item.status = "EXPIRED"
                expired.append(item)
            else:
                active_pending.append(item)
        else:
            active_pending.append(item)

    if expired:
        db.commit()

    return sorted(active_pending, key=lambda x: x.created_at or now)


@router.post("/{approval_id}/decide", response_model=ApprovalRequestResponse)
def decide_approval(
    approval_id: int,
    decision_data: ApprovalDecision,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("MANAGER", "ADMIN")),
):
    try:
        approval = db.query(ApprovalRequest).filter(ApprovalRequest.id == approval_id).with_for_update().first()
    except Exception:
        approval = db.query(ApprovalRequest).filter(ApprovalRequest.id == approval_id).first()

    if not approval:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Approval request #{approval_id} not found."
        )

    if approval.status != "PENDING":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Approval request is already in '{approval.status}' state."
        )

    now = datetime.now(timezone.utc)
    target_status = decision_data.decision.upper()
    if target_status not in ("APPROVED", "REJECTED"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Decision must be either 'APPROVED' or 'REJECTED'."
        )

    created_dt = approval.created_at
    if created_dt and created_dt.tzinfo is None:
        created_dt = created_dt.replace(tzinfo=timezone.utc)

    time_taken = int((now - created_dt).total_seconds()) if created_dt else 0

    approval.status = target_status
    approval.manager_id = current_user.id
    approval.decision_reason = decision_data.reason or f"Decided by manager {current_user.username}"
    approval.comment = decision_data.comment
    approval.decided_at = now
    approval.time_taken_seconds = time_taken

    db.commit()
    db.refresh(approval)

    APPROVAL_COUNTER.labels(status=target_status).inc()
    try:
        logger.info(
            "Manager approval decision recorded",
            approval_id=approval.id,
            decision=target_status,
            manager=current_user.username,
            time_taken_s=time_taken,
        )
    except Exception:
        pass

    return approval


@router.post("/{approval_id}/approve", response_model=ApprovalRequestResponse)
def approve_request(
    approval_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("MANAGER", "ADMIN")),
):
    return decide_approval(
        approval_id=approval_id,
        decision_data=ApprovalDecision(decision="APPROVED", reason="Approved via manager portal"),
        db=db,
        current_user=current_user,
    )


@router.post("/{approval_id}/reject", response_model=ApprovalRequestResponse)
def reject_request(
    approval_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("MANAGER", "ADMIN")),
):
    return decide_approval(
        approval_id=approval_id,
        decision_data=ApprovalDecision(decision="REJECTED", reason="Rejected via manager portal"),
        db=db,
        current_user=current_user,
    )


@router.post("/{approval_id}/remind", response_model=ApprovalRequestResponse)
def send_approval_reminder(
    approval_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("EMPLOYEE", "USER", "MANAGER", "ADMIN")),
):
    """Send reminder notification for a pending manager approval request."""
    approval = db.query(ApprovalRequest).filter(ApprovalRequest.id == approval_id).first()
    if not approval:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Approval request #{approval_id} not found."
        )
    if approval.status != "PENDING":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot send reminder for approval request in '{approval.status}' state."
        )

    approval.reminders_sent += 1
    db.commit()
    db.refresh(approval)

    try:
        from app.tasks.notification_tasks import send_approval_reminder_task
        send_approval_reminder_task.delay(approval.id, approval.action)
    except Exception:
        pass

    return approval

