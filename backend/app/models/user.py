"""
User Model.

Represents a person who logs into the system. Each User belongs to
exactly one Company, and has exactly one role determining what they
can do on the platform.
"""

import enum
import uuid
from datetime import datetime

from sqlalchemy import Column, String, Enum, Boolean, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.database.base import Base


class UserRole(str, enum.Enum):
    """Determines what a user is permitted to do on the platform."""
    ADMIN = "admin"
    BUYER = "buyer"
    VENDOR = "vendor"


class User(Base):
    """
    A person who logs into the platform on behalf of a Company.
    """

    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Foreign key to the Company this user belongs to (many users -> one company).
    company_id = Column(
        UUID(as_uuid=True),
        ForeignKey("companies.id"),
        nullable=False,
    )

    full_name = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False)

    # Only the hash is stored; the raw password is never persisted.
    password_hash = Column(String, nullable=False)

    role = Column(Enum(UserRole), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )

    # Reverse access from Company (e.g. company.users) via backref,
    # without needing to modify the Company model.
    company = relationship("Company", backref="users")