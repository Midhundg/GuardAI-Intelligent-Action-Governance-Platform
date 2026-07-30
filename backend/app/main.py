from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config.settings import settings
from app.database import Base, engine

# Import models for metadata binding
from app.models.audit import AuditLog
from app.models.approval import ApprovalRequest
from app.models.policy import Policy
from app.models.user import User
from app.models.cost_log import LLMCostLog
from app.models.prompt_scan import PromptScanLog

# Import core infrastructure
from app.middleware.logging_middleware import EnterpriseLoggingMiddleware
from app.middleware.security_middleware import SecurityHeadersMiddleware
from app.core.telemetry import init_opentelemetry

# Import routers
from app.routes.auth import router as auth_router
from app.routes.execute import router as execute_router
from app.routes.policies import router as policy_router
from app.routes.simulate import router as simulate_router
from app.routes.conflicts import router as conflict_router
from app.routes.analytics import router as analytics_router
from app.routes.recommendations import router as recommendation_router
from app.routes.approvals import router as approval_router
from app.routes.health import router as health_router
from app.routes.audit import router as audit_router
from app.routes.costs import router as cost_router
from app.routes.ws import router as ws_router
from app.routes.metrics import router as metrics_router

# Initialize Database tables
Base.metadata.create_all(bind=engine)

# Auto-seed the database with default users on startup
try:
    from seed import seed_database
    seed_database()
except Exception as e:
    print(f"Auto-seed skipped: {e}")

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="GuardAI Enterprise - Intelligent AI Governance Platform API Gateway & Security Firewall",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Optional Slowapi Rate Limiter
try:
    from slowapi import Limiter, _rate_limit_exceeded_handler
    from slowapi.util import get_remote_address
    from slowapi.errors import RateLimitExceeded

    limiter = Limiter(key_func=get_remote_address, default_limits=[f"{settings.RATE_LIMIT_PER_MINUTE}/minute"])
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
except ImportError:
    pass

# Register Enterprise Middlewares
app.add_middleware(EnterpriseLoggingMiddleware)
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize OpenTelemetry
# init_opentelemetry(app)

# Register API Routers
app.include_router(health_router)
app.include_router(metrics_router)
app.include_router(auth_router)
app.include_router(policy_router)
app.include_router(conflict_router)
app.include_router(execute_router)
app.include_router(simulate_router)
app.include_router(approval_router)
app.include_router(audit_router)
app.include_router(cost_router)
app.include_router(analytics_router)
app.include_router(recommendation_router)
app.include_router(ws_router)


@app.get("/", tags=["Health"])
def root():
    return {
        "message": f"Welcome to {settings.APP_NAME} 🚀",
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT,
        "docs": "/docs",
    }