from pydantic import BaseModel


class PolicyConflict(BaseModel):
    policy_1: str
    policy_2: str
    reason: str