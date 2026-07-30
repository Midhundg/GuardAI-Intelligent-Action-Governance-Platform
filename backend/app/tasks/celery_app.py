from app.config.settings import settings

try:
    from celery import Celery
    celery_app = Celery(
        "guardai_tasks",
        broker=settings.CELERY_BROKER_URL,
        backend=settings.CELERY_RESULT_BACKEND,
    )

    celery_app.conf.update(
        task_serializer="json",
        accept_content=["json"],
        result_serializer="json",
        timezone="UTC",
        enable_utc=True,
        task_track_started=True,
    )
except ImportError:
    class DummyCeleryApp:
        def __init__(self):
            self.conf = {}
        def task(self, *args, **kwargs):
            def decorator(fn):
                fn.delay = lambda *a, **kw: fn(*a, **kw)
                return fn
            return decorator

    celery_app = DummyCeleryApp()
