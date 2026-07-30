from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.dependencies import get_db
from app.services.analytics import AnalyticsService

router = APIRouter(
    prefix="/analytics",
    tags=["Governance Analytics"],
)


@router.get("/dashboard")
def get_dashboard(db: Session = Depends(get_db)):
    return AnalyticsService.get_dashboard(db)