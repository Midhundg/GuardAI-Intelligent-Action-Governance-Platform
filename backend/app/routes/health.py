from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.config.settings import settings
from app.dependencies import get_db

router = APIRouter(
    prefix="",
    tags=["Health & Monitoring"],
)


@router.get("/health")
def health_check(db: Session = Depends(get_db)):
    """Comprehensive service health report covering DB, Redis, Celery, and LLM API config."""
    db_status = "unhealthy"
    try:
        db.execute(text("SELECT 1"))
        db_status = "connected"
    except Exception as e:
        db_status = f"error: {str(e)}"

    redis_status = "disconnected"
    try:
        import redis
        r = redis.Redis.from_url(settings.REDIS_URL, socket_timeout=1.0)
        if r.ping():
            redis_status = "connected"
    except Exception:
        redis_status = "offline (using in-memory fallback)"

    llm_status = "configured" if (settings.OPENAI_API_KEY or settings.ANTHROPIC_API_KEY) else "unconfigured (using mock mode)"
    queue_status = "configured" if settings.CELERY_BROKER_URL else "unconfigured"

    is_overall_healthy = (db_status == "connected")

    return {
        "status": "healthy" if is_overall_healthy else "degraded",
        "service": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT,
        "dependencies": {
            "database": db_status,
            "redis": redis_status,
            "queue": queue_status,
            "llm_provider": llm_status,
        },
    }


@router.get("/ready")
def readiness_check(db: Session = Depends(get_db)):
    """Readiness probe for Kubernetes / Load balancer target group."""
    try:
        db.execute(text("SELECT 1"))
        return {"status": "ready", "ready": True}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Database connection failed: {str(e)}",
        )


@router.get("/live")
def liveness_check():
    """Liveness probe confirming FastAPI web worker is serving HTTP requests."""
    return {"status": "alive", "live": True}
