"""
Bid Model.

Represents a single price submitted by a Vendor Company during a live
Auction. Stores raw bid facts only — rank, current-lowest-bid, and
winner determination are derived values computed in the service layer,
not stored here.
"""

import uuid
from datetime import datetime

from sqlalchemy import Column, Numeric, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.database.base import Base


class Bid(Base):
    """
    A price offer submitted by a Vendor Company for a specific Auction.
    """

    __tablename__ = "bids"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # The auction this bid was placed on (one auction -> many bids).
    auction_id = Column(
        UUID(as_uuid=True),
        ForeignKey("auctions.id"),
        nullable=False,
    )

    # The vendor company that placed this bid (one vendor -> many bids).
    vendor_company_id = Column(
        UUID(as_uuid=True),
        ForeignKey("companies.id"),
        nullable=False,
    )

    bid_amount = Column(Numeric(12, 2), nullable=False)
    bid_time = Column(DateTime, default=datetime.utcnow, nullable=False)

    auction = relationship("Auction")
    vendor_company = relationship("Company")