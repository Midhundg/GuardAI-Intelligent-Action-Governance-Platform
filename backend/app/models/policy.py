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
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)

    # Policy Matching
    action = Column(String(100), nullable=False)
    condition_type = Column(String(100), nullable=False)

    # Store as string for flexibility
    condition_value = Column(String(255), nullable=False)

    # Decision
    decision = Column(String(50), nullable=False)

    # Risk Metadata
    severity = Column(
        String(20),
        default="MEDIUM",
        nullable=False,
    )

    enabled = Column(
        Boolean,
        default=True,
        nullable=False,
    )

    # Policy Versioning
    version = Column(
        Integer,
        default=1,
        nullable=False,
    )


    # Approval Workflow (next feature)
    requires_approval = Column(
        Boolean,
        default=False,
        nullable=False,
    )

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