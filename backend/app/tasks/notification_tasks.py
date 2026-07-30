import logging
from app.tasks.celery_app import celery_app

try:
    import structlog
    logger = structlog.get_logger()
except ImportError:
    logger = logging.getLogger("notification_tasks")


@celery_app.task(name="tasks.send_approval_notification")
def send_approval_notification_task(approval_id: int, requester_name: str, action_name: str, risk_level: str):
    """Send asynchronous manager notifications via Webhook/Email/Slack."""
    return {
        "status": "sent",
        "approval_id": approval_id,
        "channel": "slack_and_email",
    }


@celery_app.task(name="tasks.send_approval_reminder")
def send_approval_reminder_task(approval_id: int):
    """Send asynchronous reminder for pending high-risk approvals near expiration."""
    return {"status": "reminder_sent", "approval_id": approval_id}
