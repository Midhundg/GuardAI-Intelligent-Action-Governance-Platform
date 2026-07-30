from pydantic import BaseModel, Field


class ActionRequest(BaseModel):
    action: str = Field(..., example="delete_database")
    record_count: int = Field(default=0, example=500)
    external: bool = Field(default=False)
    classification: str | None = Field(default=None)


class PolicyDecision(BaseModel):
    decision: str
    reason: str

    matched_policy: int | None

    risk_score: int
    risk_level: str
    confidence: float

    explanation: list[str]

    trace: list[str]

    model_config = {
        "from_attributes": True
    }


class ActionResponse(BaseModel):
    request_id: str

    request: ActionRequest

    result: PolicyDecision