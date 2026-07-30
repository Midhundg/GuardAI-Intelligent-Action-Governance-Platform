from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.dependencies import (
    get_db,
    require_roles,
)
from app.models.user import User
from app.services.recommendation_engine import RecommendationEngine

router = APIRouter(
    prefix="/recommendations",
    tags=["AI Recommendations"],
)


@router.get("/")
def get_recommendations(
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles("ADMIN", "MANAGER")
    ),
):
    return RecommendationEngine.generate(db)