from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class PolicyBase(BaseModel):
    name: str
    description: Optional[str] = None

    action: str
    condition_type: str
    condition_value: str

    decision: str

    severity: str = "MEDIUM"

    enabled: bool = True

    requires_approval: bool = False


class PolicyCreate(PolicyBase):
    pass


class PolicyUpdate(PolicyBase):
    pass


class PolicyResponse(PolicyBase):
    id: int
    version: int

    created_at: datetime
    updated_at: datetime

    model_config = {
        "from_attributes": True
    }