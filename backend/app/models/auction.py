"""
Auction Model.

Represents a reverse auction created by a Buyer Company, in which
invited Vendor Companies compete by submitting progressively lower bids.
This is the central entity of the procurement platform.
"""

import enum
import uuid
from datetime import datetime

from sqlalchemy import Column, String, Integer, Numeric, DateTime, Enum, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.database.base import Base


class AuctionStatus(str, enum.Enum):
    """Lifecycle state of an auction."""
    DRAFT = "draft"
    LIVE = "live"
    ENDED = "ended"
    AWARDED = "awarded"
    CANCELLED = "cancelled"


class Auction(Base):
    """
    A reverse auction created by a Buyer Company for a procurement need.
    """

    __tablename__ = "auctions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # The Buyer Company that created this auction (one buyer -> many auctions).
    buyer_company_id = Column(
        UUID(as_uuid=True),
        ForeignKey("companies.id"),
        nullable=False,
    )

    title = Column(String, nullable=False)
    description = Column(String, nullable=False)

    # What is being procured
    material_name = Column(String, nullable=False)
    quantity = Column(Integer, nullable=False)
    unit = Column(String, nullable=False)

    # Buyer-defined starting price; vendors must bid below the current lowest.
    base_price = Column(Numeric(12, 2), nullable=False)

    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime, nullable=False)

    status = Column(Enum(AuctionStatus), nullable=False, default=AuctionStatus.DRAFT)

    # Set only after the buyer manually awards the auction; unknown until then.
    winner_company_id = Column(
        UUID(as_uuid=True),
        ForeignKey("companies.id"),
        nullable=True,
    )

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )

    # Relationships to Company, referenced explicitly since two foreign
    # keys point to the same table (buyer vs. winner).
    buyer_company = relationship("Company", foreign_keys=[buyer_company_id])
    winner_company = relationship("Company", foreign_keys=[winner_company_id])