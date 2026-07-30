import time
import uuid
import json
import logging
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

try:
    import structlog
    logger = structlog.get_logger()
except ImportError:
    class DummyStructLogger:
        def info(self, msg, **kwargs):
            logging.info(f"{msg}: {json.dumps(kwargs)}")
        def warning(self, msg, **kwargs):
            logging.warning(f"{msg}: {json.dumps(kwargs)}")
        def error(self, msg, **kwargs):
            logging.error(f"{msg}: {json.dumps(kwargs)}")
    logger = DummyStructLogger()


class EnterpriseLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware for structured JSON logging, correlation IDs, and latency tracking."""

    async def dispatch(self, request: Request, call_next):
        start_time = time.perf_counter()

        request_id = str(uuid.uuid4())
        correlation_id = request.headers.get("X-Correlation-ID", request_id)
        agent_id = request.headers.get("X-Agent-ID", "unknown_agent")

        request.state.request_id = request_id
        request.state.correlation_id = correlation_id
        request.state.agent_id = agent_id

        try:
            import structlog
            structlog.contextvars.clear_contextvars()
            structlog.contextvars.bind_contextvars(
                request_id=request_id,
                correlation_id=correlation_id,
                agent_id=agent_id,
                path=request.url.path,
                method=request.method,
            )
        except Exception:
            pass

        response = await call_next(request)

        process_time_ms = round((time.perf_counter() - start_time) * 1000, 2)
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Correlation-ID"] = correlation_id
        response.headers["X-Process-Time"] = f"{process_time_ms}ms"

        logger.info(
            "HTTP Request Processed",
            status_code=response.status_code,
            duration_ms=process_time_ms,
        )

        return response
