from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base


class ApprovalRequest(Base):
    __tablename__ = "approval_requests"

    id = Column(Integer, primary_key=True, index=True)
    request_id = Column(String(100), unique=True, nullable=False, index=True)
    action = Column(String(100), nullable=False, index=True)

    requested_by = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=False,
        index=True,
    )

    status = Column(
        String(50),
        default="PENDING",
        nullable=False,
        index=True,
    )

    manager_id = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=True,
        index=True,
    )

    decision_reason = Column(Text, nullable=True)
    comment = Column(Text, nullable=True)
    time_taken_seconds = Column(Integer, nullable=True)
    reminders_sent = Column(Integer, default=0, nullable=False)

    expires_at = Column(
        DateTime(timezone=True),
        nullable=True,
    )

    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
    )

    decided_at = Column(
        DateTime(timezone=True),
        nullable=True,
    )

    requester = relationship(
        "User",
        foreign_keys=[requested_by],
    )

    manager = relationship(
        "User",
        foreign_keys=[manager_id],
    )