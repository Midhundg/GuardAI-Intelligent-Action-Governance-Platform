from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Integer,
    String,
    Text,
)
from sqlalchemy.sql import func

from app.database import Base


class Policy(Base):
    __tablename__ = "policies"

    id = Column(Integer, primary_key=True, index=True)

    # Basic Information
    name = Column(String(100), nullable=False, index=True)
    description = Column(Text, nullable=True)

    # Policy Matching
    action = Column(String(100), nullable=False, index=True)
    condition_type = Column(String(100), nullable=False, index=True)

    # Store as string for flexibility
    condition_value = Column(String(255), nullable=False)

    # Decision
    decision = Column(String(50), nullable=False, index=True)

    # Risk Metadata
    severity = Column(
        String(20),
        default="MEDIUM",
        nullable=False,
        index=True,
    )

    enabled = Column(
        Boolean,
        default=True,
        nullable=False,
        index=True,
    )

    # Policy Versioning
    version = Column(
        Integer,
        default=1,
        nullable=False,
    )

    # Approval Workflow
    requires_approval = Column(
        Boolean,
        default=False,
        nullable=False,
    )

    is_deleted = Column(
        Boolean,
        default=False,
        nullable=False,
        index=True,
    )

    created_by = Column(String(100), nullable=True)
    updated_by = Column(String(100), nullable=True)

    # Audit Fields
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
    )

    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )