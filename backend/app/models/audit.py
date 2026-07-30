from sqlalchemy import Column, Integer, String, Text
from app.database import Base


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    request_id = Column(String, index=True)
    timestamp = Column(String)
    action = Column(String)
    request = Column(Text)
    decision = Column(String)
    reason = Column(Text)