import logging
from app.tasks.celery_app import celery_app
from app.database import SessionLocal
from app.services.analytics import AnalyticsService

try:
    import structlog
    logger = structlog.get_logger()
except ImportError:
    logger = logging.getLogger("analytics_tasks")


@celery_app.task(name="tasks.aggregate_daily_analytics")
def aggregate_daily_analytics_task():
    """Background task to pre-calculate and cache daily governance analytics."""
    db = SessionLocal()
    try:
        data = AnalyticsService.get_dashboard(db)
        try:
            from app.core.cache import cache
            cache.set("analytics_dashboard_cache", data, ttl_seconds=300)
        except Exception:
            pass
        return {"status": "success", "analytics": data}
    except Exception as e:
        return {"status": "failed", "error": str(e)}
    finally:
        db.close()
