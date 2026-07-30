from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.dependencies import get_db
from app.services.recommendation_engine import RecommendationEngine

router = APIRouter(
    prefix="/recommendations",
    tags=["AI Recommendations"],
)


@router.get("/")
def get_recommendations(db: Session = Depends(get_db)):
    return RecommendationEngine.generate(db)