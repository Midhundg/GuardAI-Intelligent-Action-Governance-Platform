from fastapi import APIRouter
from fastapi.responses import Response
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST

router = APIRouter(
    tags=["Observability"],
)


@router.get("/metrics")
def get_prometheus_metrics():
    """Prometheus telemetry metrics endpoint."""
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)
