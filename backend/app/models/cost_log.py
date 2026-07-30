from sqlalchemy import Column, Integer, String, Float, DateTime
from sqlalchemy.sql import func
from app.database import Base


class LLMCostLog(Base):
    __tablename__ = "llm_cost_logs"

    id = Column(Integer, primary_key=True, index=True)
    request_id = Column(String(100), index=True)
    user_id = Column(Integer, nullable=True, index=True)
    provider = Column(String(50), nullable=False, index=True)  # OpenAI, Anthropic, Bedrock
    model_name = Column(String(100), nullable=False, index=True)

    prompt_tokens = Column(Integer, default=0, nullable=False)
    completion_tokens = Column(Integer, default=0, nullable=False)
    total_tokens = Column(Integer, default=0, nullable=False)

    estimated_cost_usd = Column(Float, default=0.0, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
