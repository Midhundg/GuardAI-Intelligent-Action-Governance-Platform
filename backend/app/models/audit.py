from sqlalchemy import Column, Integer, String, Text, Float, DateTime
from sqlalchemy.sql import func
from app.database import Base


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    request_id = Column(String(100), index=True)
    correlation_id = Column(String(100), index=True, nullable=True)
    timestamp = Column(String(100), index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    action = Column(String(100), index=True)
    request = Column(Text)
    decision = Column(String(50), index=True)
    reason = Column(Text)

    user_id = Column(Integer, nullable=True, index=True)
    agent_id = Column(String(100), nullable=True, index=True)
    policy_id = Column(Integer, nullable=True, index=True)

    risk_score = Column(Integer, nullable=True, index=True)
    risk_level = Column(String(20), nullable=True, index=True)
    execution_time_ms = Column(Float, nullable=True)