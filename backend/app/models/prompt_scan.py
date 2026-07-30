from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime
from sqlalchemy.sql import func
from app.database import Base


class PromptScanLog(Base):
    __tablename__ = "prompt_scan_logs"

    id = Column(Integer, primary_key=True, index=True)
    request_id = Column(String(100), index=True)
    user_id = Column(Integer, nullable=True, index=True)
    has_warnings = Column(Boolean, default=False, index=True)
    detected_threats = Column(Text, nullable=True)  # JSON array string of detected items
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
