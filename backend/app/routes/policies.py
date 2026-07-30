from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.dependencies import get_db
from app.models.policy import Policy
from app.schemas.policy import (
    PolicyCreate,
    PolicyResponse,
)

router = APIRouter(
    prefix="/policies",
    tags=["Policies"],
)


@router.get("/", response_model=list[PolicyResponse])
def get_policies(db: Session = Depends(get_db)):
    return db.query(Policy).all()


@router.post("/", response_model=PolicyResponse)
def create_policy(
    policy: PolicyCreate,
    db: Session = Depends(get_db),
):
    db_policy = Policy(
        name=policy.name,
        description=policy.description,
        action=policy.action,
        condition_type=policy.condition_type,
        condition_value=policy.condition_value,
        decision=policy.decision,
        severity=policy.severity,
        enabled=policy.enabled,
        version=1,
        requires_approval=policy.requires_approval,
    )

    db.add(db_policy)
    db.commit()
    db.refresh(db_policy)

    return db_policy