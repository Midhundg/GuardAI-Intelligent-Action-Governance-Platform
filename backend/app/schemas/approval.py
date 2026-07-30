from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class ApprovalRequestResponse(BaseModel):
    id: int
    request_id: str
    action: str
    status: str
    decision_reason: Optional[str] = None
    comment: Optional[str] = None
    created_at: datetime
    decided_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    time_taken_seconds: Optional[int] = None
    requested_by: int
    manager_id: Optional[int] = None

    model_config = {
        "from_attributes": True
    }


class ApprovalDecision(BaseModel):
    decision: str = Field(..., json_schema_extra={"example": "APPROVED"})  # APPROVED or REJECTED
    reason: Optional[str] = Field(default=None, json_schema_extra={"example": "Verified change ticket #4021"})
    comment: Optional[str] = Field(default=None, json_schema_extra={"example": "Approved for night window release."})