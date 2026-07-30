from pydantic import BaseModel
from typing import Optional


class SimulationRequest(BaseModel):
    action: str
    record_count: int = 0
    external: bool = False
    classification: Optional[str] = None


class SimulationResponse(BaseModel):
    simulation_id: str

    decision: str
    reason: str

    matched_policy: int | None

    risk_score: int
    risk_level: str

    confidence: float

    explanation: list[str]

    evaluation_time_ms: float

    would_execute: bool