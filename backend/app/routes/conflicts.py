from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.dependencies import get_db
from app.models.policy import Policy
from app.core.conflict_engine import ConflictEngine
from app.schemas.conflict import PolicyConflict

router = APIRouter(
    prefix="/policies",
    tags=["Policies"]
)


@router.get(
    "/conflicts",
    response_model=list[PolicyConflict]
)
def get_policy_conflicts(
    db: Session = Depends(get_db),
):
    policies = db.query(Policy).filter(
        Policy.enabled == True
    ).all()

    engine = ConflictEngine()

    return engine.find_conflicts(policies)