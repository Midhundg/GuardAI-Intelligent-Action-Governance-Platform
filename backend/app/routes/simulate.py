from fastapi import APIRouter, Depends

from app.core.simulation_engine import SimulationEngine
from app.dependencies import require_roles
from app.models.user import User
from app.schemas.simulation import (
    SimulationRequest,
    SimulationResponse,
)

router = APIRouter(
    prefix="/simulate",
    tags=["Simulation"],
)

simulation_engine = SimulationEngine()


@router.post("/", response_model=SimulationResponse)
def simulate_action(
    request: SimulationRequest,
    current_user: User = Depends(
        require_roles("USER", "MANAGER", "ADMIN")
    ),
):
    result = simulation_engine.simulate(
        request.model_dump()
    )

    return SimulationResponse(
        simulation_id=result["simulation_id"],
        decision=result["decision"],
        reason=result["reason"],
        matched_policy=result["matched_policy"],
        risk_score=result["risk_score"],
        risk_level=result["risk_level"],
        confidence=result["confidence"],
        explanation=result["explanation"],
        evaluation_time_ms=result["evaluation_time_ms"],
        would_execute=result["would_execute"],
    )