import io
import csv
from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy import func, desc

from app.dependencies import get_db, require_roles
from app.models.audit import AuditLog
from app.models.approval import ApprovalRequest
from app.models.policy import Policy
from app.models.user import User

router = APIRouter(
    prefix="/audit",
    tags=["Audit & Compliance"],
)


@router.get("/logs")
def get_audit_logs(
    limit: int = Query(default=50, ge=1, le=500),
    decision: Optional[str] = None,
    action: Optional[str] = None,
    user_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("ADMIN", "AUDITOR", "MANAGER")),
):
    """Retrieve audit logs with optional filtering."""
    query = db.query(AuditLog)
    if decision:
        query = query.filter(AuditLog.decision == decision.lower())
    if action:
        query = query.filter(AuditLog.action == action)
    if user_id:
        query = query.filter(AuditLog.user_id == user_id)

    logs = query.order_by(AuditLog.id.desc()).limit(limit).all()
    return logs


@router.get("/top-blocked")
def get_top_blocked_actions(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("ADMIN", "AUDITOR", "MANAGER")),
):
    """Analytics API: Top blocked actions count."""
    results = (
        db.query(AuditLog.action, func.count(AuditLog.id).label("count"))
        .filter(AuditLog.decision == "block")
        .group_by(AuditLog.action)
        .order_by(desc("count"))
        .limit(10)
        .all()
    )
    return [{"action": r[0], "count": r[1]} for r in results]


@router.get("/most-violated-policies")
def get_most_violated_policies(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("ADMIN", "AUDITOR", "MANAGER")),
):
    """Analytics API: Most violated policies."""
    results = (
        db.query(AuditLog.policy_id, func.count(AuditLog.id).label("violations"))
        .filter(AuditLog.decision == "block", AuditLog.policy_id != None)
        .group_by(AuditLog.policy_id)
        .order_by(desc("violations"))
        .limit(10)
        .all()
    )
    policy_details = []
    for pid, count in results:
        policy = db.query(Policy).filter(Policy.id == pid).first()
        policy_details.append({
            "policy_id": pid,
            "policy_name": policy.name if policy else f"Policy #{pid}",
            "severity": policy.severity if policy else "HIGH",
            "violations": count,
        })
    return policy_details


@router.get("/top-users")
def get_top_active_users(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("ADMIN", "AUDITOR")),
):
    """Analytics API: Top users by request volume."""
    results = (
        db.query(AuditLog.user_id, func.count(AuditLog.id).label("requests"))
        .filter(AuditLog.user_id != None)
        .group_by(AuditLog.user_id)
        .order_by(desc("requests"))
        .limit(10)
        .all()
    )
    user_metrics = []
    for uid, count in results:
        usr = db.query(User).filter(User.id == uid).first()
        user_metrics.append({
            "user_id": uid,
            "username": usr.username if usr else f"User #{uid}",
            "role": usr.role if usr else "USER",
            "total_requests": count,
        })
    return user_metrics


@router.get("/risk-distribution")
def get_risk_distribution(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("ADMIN", "AUDITOR", "MANAGER")),
):
    """Analytics API: Risk level distribution count."""
    results = (
        db.query(AuditLog.risk_level, func.count(AuditLog.id).label("count"))
        .group_by(AuditLog.risk_level)
        .all()
    )
    dist = {"LOW": 0, "MEDIUM": 0, "HIGH": 0, "CRITICAL": 0}
    for level, count in results:
        if level in dist:
            dist[level] = count
    return dist


@router.get("/average-approval-time")
def get_average_approval_time(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("ADMIN", "AUDITOR", "MANAGER")),
):
    """Analytics API: Average approval time in seconds."""
    avg_seconds = (
        db.query(func.avg(ApprovalRequest.time_taken_seconds))
        .filter(ApprovalRequest.status.in_(["APPROVED", "REJECTED"]))
        .scalar()
    )
    return {
        "average_approval_time_seconds": round(float(avg_seconds or 0), 2),
        "average_approval_time_minutes": round(float(avg_seconds or 0) / 60.0, 2),
    }


@router.get("/daily-approvals")
def get_daily_approvals(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("ADMIN", "AUDITOR", "MANAGER")),
):
    """Analytics API: Daily approvals count aggregated by date and status."""
    results = (
        db.query(
            func.date(ApprovalRequest.created_at).label("date"),
            ApprovalRequest.status,
            func.count(ApprovalRequest.id).label("count"),
        )
        .group_by("date", ApprovalRequest.status)
        .order_by(desc("date"))
        .limit(30)
        .all()
    )
    daily_map = {}
    for date_str, status_name, cnt in results:
        d = str(date_str) if date_str else "Today"
        if d not in daily_map:
            daily_map[d] = {"date": d, "approved": 0, "rejected": 0, "pending": 0, "expired": 0, "total": 0}
        st = str(status_name).lower()
        if st in daily_map[d]:
            daily_map[d][st] += cnt
        daily_map[d]["total"] += cnt
    return list(daily_map.values())



@router.get("/export/csv")
def export_audit_csv(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("ADMIN", "AUDITOR")),
):
    """Export audit log trail as CSV stream."""
    logs = db.query(AuditLog).order_by(AuditLog.id.desc()).all()
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "ID", "Request ID", "Timestamp", "Action", "Decision", "Reason",
        "User ID", "Agent ID", "Policy ID", "Risk Score", "Risk Level", "Latency (ms)"
    ])

    for log in logs:
        writer.writerow([
            log.id, log.request_id, log.timestamp, log.action, log.decision, log.reason,
            log.user_id, log.agent_id, log.policy_id, log.risk_score, log.risk_level, log.execution_time_ms
        ])

    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=guardai_audit_export.csv"}
    )
