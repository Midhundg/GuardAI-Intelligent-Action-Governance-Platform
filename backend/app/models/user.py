from sqlalchemy import Boolean, Column, DateTime, Integer, String
from sqlalchemy.sql import func

from app.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(100), unique=True, nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    role = Column(
        String(50),
        nullable=False,
        default="USER",
        index=True,
    )
    department = Column(
        String(100),
        nullable=True,
    )
    is_active = Column(
        Boolean,
        default=True,
        nullable=False,
    )
    is_deleted = Column(
        Boolean,
        default=False,
        nullable=False,
        index=True,
    )
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
    )
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )
    last_login = Column(
        DateTime(timezone=True),
        nullable=True,
    )
    created_by = Column(String(100), nullable=True)
    updated_by = Column(String(100), nullable=True)