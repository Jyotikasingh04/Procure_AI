"""
Company Model.

Represents a registered company on the platform, which can be either
a Buyer or a Vendor. Both roles share the same registration fields,
so a single table with a `company_type` column avoids duplication.
"""

import enum
import uuid
from datetime import datetime

from sqlalchemy import Column, String, Enum, DateTime
from sqlalchemy.dialects.postgresql import UUID

from app.database.base import Base


class CompanyType(str, enum.Enum):
    """Distinguishes whether a company is a Buyer or a Vendor."""
    BUYER = "buyer"
    VENDOR = "vendor"


class VerificationStatus(str, enum.Enum):
    """Tracks the admin verification state of a company's registration."""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class Company(Base):
    """
    A Buyer or Vendor company registered on the platform.
    """

    __tablename__ = "companies"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    company_name = Column(String(255), nullable=False)
    company_type = Column(Enum(CompanyType), nullable=False)

    # Legal identifiers
    gst_number = Column(String(15), unique=True, nullable=False)
    pan_number = Column(String(10), unique=True, nullable=False)
    cin_number = Column(String, nullable=True)  # Not all companies have a CIN

    # Contact details
    official_email = Column(
    String,
    unique=True,
    nullable=False
)
    phone_number = Column(String, nullable=False)

    # Address
    address = Column(String, nullable=False)
    city = Column(String, nullable=False)
    state = Column(String, nullable=False)
    country = Column(
    String,
    default="India",
    nullable=False
)
    pincode = Column(String, nullable=False)

    # Admin verification workflow
    verification_status = Column(
        Enum(VerificationStatus),
        nullable=False,
        default=VerificationStatus.PENDING,
    )

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )