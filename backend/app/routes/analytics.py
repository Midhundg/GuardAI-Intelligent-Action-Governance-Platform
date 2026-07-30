from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.dependencies import get_db, require_roles
from app.models.user import User
from app.services.analytics import AnalyticsService

router = APIRouter(
    prefix="/analytics",
    tags=["Governance Analytics"],
)


@router.get("/dashboard")
def get_dashboard(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("ADMIN", "AUDITOR", "MANAGER")),
):
    """Retrieve full governance analytics dashboard summary."""
    return AnalyticsService.get_dashboard(db)


@router.get("/daily-requests")
def get_daily_requests(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("ADMIN", "AUDITOR", "MANAGER")),
):
    """Analytics API: Daily incoming requests count."""
    return AnalyticsService.get_daily_requests(db)


@router.get("/blocked-actions")
def get_blocked_actions_count(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("ADMIN", "AUDITOR", "MANAGER")),
):
    """Analytics API: Total blocked actions count."""
    dash = AnalyticsService.get_dashboard(db)
    return {"blocked_actions": dash["blocked_actions"]}


@router.get("/approval-success-rate")
def get_approval_success_rate(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("ADMIN", "AUDITOR", "MANAGER")),
):
    """Analytics API: Manager approval success rate percentage."""
    dash = AnalyticsService.get_dashboard(db)
    return {
        "total_approvals": dash["total_approvals"],
        "approved_count": dash["approved_count"],
        "rejected_count": dash["rejected_count"],
        "approval_success_rate": dash["approval_success_rate"],
    }


@router.get("/average-latency")
def get_average_latency(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("ADMIN", "AUDITOR", "MANAGER")),
):
    """Analytics API: Average latency in ms."""
    dash = AnalyticsService.get_dashboard(db)
    return {"average_latency_ms": dash["average_latency_ms"]}


@router.get("/most-used-agent")
def get_most_used_agent(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("ADMIN", "AUDITOR", "MANAGER")),
):
    """Analytics API: Most used agent ID."""
    dash = AnalyticsService.get_dashboard(db)
    return {"most_used_agent": dash["most_used_agent"]}


@router.get("/most-used-policy")
def get_most_used_policy(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("ADMIN", "AUDITOR", "MANAGER")),
):
    """Analytics API: Most frequently triggered policy rule."""
    dash = AnalyticsService.get_dashboard(db)
    return {"most_used_policy": dash["most_used_policy"]}