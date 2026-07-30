from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional, Union


class ActionRequest(BaseModel):
    action: str = Field(..., json_schema_extra={"example": "delete_database"})
    record_count: int = Field(default=0, json_schema_extra={"example": 500})
    external: bool = Field(default=False)
    classification: Optional[str] = Field(default=None)
    prompt: Optional[str] = Field(default=None, json_schema_extra={"example": "Clean old data records from server"})
    email_id: Optional[str] = Field(default=None, json_schema_extra={"example": "user@company.com"})
    path: Optional[str] = Field(default=None, json_schema_extra={"example": "/var/log/syslog"})
    agent_id: Optional[str] = Field(default="coding_agent", json_schema_extra={"example": "devops_agent"})
    model_name: Optional[str] = Field(default="gpt-4o-mini", json_schema_extra={"example": "gpt-4o-mini"})


class PolicyDecision(BaseModel):
    decision: str
    reason: str

    matched_policy: Union[int, str, None] = None
    matched_policy_name: Optional[str] = None
    suggested_alternative: Optional[str] = None

    risk_score: int
    risk_level: str
    confidence: float

    explanation: List[str]
    factors_considered: Optional[List[str]] = Field(default_factory=list)
    why_risky: Optional[List[str]] = Field(default_factory=list)
    recommended_mitigation: Optional[List[str]] = Field(default_factory=list)

    trace: List[str]
    ai_explanation: Optional[Dict[str, Any]] = None
    security_scan: Optional[Dict[str, Any]] = None

    model_config = {
        "from_attributes": True
    }


class ActionResponse(BaseModel):
    request_id: str
    correlation_id: Optional[str] = None

    status: str = "COMPLETED"
    approval_request_id: Optional[int] = None
    message: Optional[str] = None

    request: ActionRequest
    result: PolicyDecision
    warnings: Optional[List[str]] = Field(default_factory=list)