import logging
from app.tasks.celery_app import celery_app
from app.services.audit_logger import AuditLogger

try:
    import structlog
    logger = structlog.get_logger()
except ImportError:
    logger = logging.getLogger("audit_tasks")


@celery_app.task(name="tasks.log_audit_event")
def log_audit_event_task(request_id: str, request_data: dict, result_data: dict, extra_context: dict = None):
    """Background task to record audit logs off the critical HTTP path."""
    try:
        audit_logger = AuditLogger()
        audit_logger.log(request_id, request_data, result_data)
        return {"status": "success", "request_id": request_id}
    except Exception as e:
        return {"status": "failed", "error": str(e)}
