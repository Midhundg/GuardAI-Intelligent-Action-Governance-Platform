from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.dependencies import get_db, require_roles
from app.models.cost_log import LLMCostLog
from app.models.user import User

router = APIRouter(
    prefix="/costs",
    tags=["LLM Cost Tracking"],
)


@router.get("/summary")
def get_cost_summary(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("ADMIN", "MANAGER", "AUDITOR")),
):
    """Token usage and estimated cost breakdown across OpenAI, Anthropic, Bedrock."""
    total_prompt_tokens = db.query(func.sum(LLMCostLog.prompt_tokens)).scalar() or 0
    total_completion_tokens = db.query(func.sum(LLMCostLog.completion_tokens)).scalar() or 0
    total_tokens = db.query(func.sum(LLMCostLog.total_tokens)).scalar() or 0
    total_cost_usd = db.query(func.sum(LLMCostLog.estimated_cost_usd)).scalar() or 0.0

    # Provider breakdown
    provider_results = (
        db.query(
            LLMCostLog.provider,
            func.sum(LLMCostLog.total_tokens).label("tokens"),
            func.sum(LLMCostLog.estimated_cost_usd).label("cost"),
        )
        .group_by(LLMCostLog.provider)
        .all()
    )

    provider_breakdown = {}
    for prov, tok, cost in provider_results:
        provider_breakdown[prov] = {
            "tokens": tok or 0,
            "cost_usd": round(cost or 0.0, 4),
        }

    return {
        "total_prompt_tokens": total_prompt_tokens,
        "total_completion_tokens": total_completion_tokens,
        "total_tokens": total_tokens,
        "total_cost_usd": round(total_cost_usd, 4),
        "provider_breakdown": provider_breakdown,
    }


@router.get("/per-user")
def get_user_cost_breakdown(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("ADMIN", "AUDITOR")),
):
    """Cost breakdown grouped by user."""
    results = (
        db.query(
            LLMCostLog.user_id,
            func.sum(LLMCostLog.total_tokens).label("tokens"),
            func.sum(LLMCostLog.estimated_cost_usd).label("cost"),
        )
        .group_by(LLMCostLog.user_id)
        .all()
    )

    user_costs = []
    for uid, tok, cost in results:
        usr = db.query(User).filter(User.id == uid).first() if uid else None
        user_costs.append({
            "user_id": uid,
            "username": usr.username if usr else "AI Agent / System",
            "total_tokens": tok or 0,
            "estimated_cost_usd": round(cost or 0.0, 4),
        })
    return user_costs


@router.get("/daily")
def get_daily_cost_breakdown(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("ADMIN", "MANAGER", "AUDITOR")),
):
    """Daily token consumption and cost usage."""
    results = (
        db.query(
            func.date(LLMCostLog.created_at).label("day"),
            func.sum(LLMCostLog.total_tokens).label("tokens"),
            func.sum(LLMCostLog.estimated_cost_usd).label("cost"),
        )
        .group_by("day")
        .order_by("day")
        .limit(30)
        .all()
    )
    return [
        {
            "date": str(day) if day else "Today",
            "total_tokens": tokens or 0,
            "estimated_cost_usd": round(cost or 0.0, 4),
        }
        for day, tokens, cost in results
    ]


@router.get("/monthly")
def get_monthly_cost_breakdown(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("ADMIN", "MANAGER", "AUDITOR")),
):
    """Monthly token consumption and cost usage."""
    results = (
        db.query(
            func.strftime("%Y-%m", LLMCostLog.created_at).label("month"),
            func.sum(LLMCostLog.total_tokens).label("tokens"),
            func.sum(LLMCostLog.estimated_cost_usd).label("cost"),
        )
        .group_by("month")
        .order_by("month")
        .limit(12)
        .all()
    )
    return [
        {
            "month": str(month) if month else "Current Month",
            "total_tokens": tokens or 0,
            "estimated_cost_usd": round(cost or 0.0, 4),
        }
        for month, tokens, cost in results
    ]

