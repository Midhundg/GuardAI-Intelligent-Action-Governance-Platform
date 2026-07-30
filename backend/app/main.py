from fastapi import FastAPI

from app.config.settings import settings
from app.database import Base, engine

# Import models so SQLAlchemy creates the tables
from app.models.audit import AuditLog
from app.models.policy import Policy

# Import routers
from app.routes.execute import router as execute_router
from app.routes.policies import router as policy_router
from app.routes.simulate import router as simulate_router
from app.routes.conflicts import router as conflict_router
from app.routes.analytics import router as analytics_router
from app.routes.recommendations import router as recommendation_router

# Create database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="GuardAI - Intelligent Action Governance Platform",
)


@app.get("/")
def root():
    return {
        "message": f"Welcome to {settings.APP_NAME} 🚀",
        "version": settings.APP_VERSION,
    }


@app.get("/health")
def health():
    return {"status": "healthy"}


# Register routers
app.include_router(policy_router)
app.include_router(conflict_router)
app.include_router(execute_router)
app.include_router(simulate_router)
app.include_router(analytics_router)
app.include_router(recommendation_router)