"""
Bid Schemas.

Pydantic request/response models for placing a bid and for a buyer
reviewing bids on their auction.
vendor_company_id is intentionally NOT part of BidCreateRequest — it
is derived from the authenticated user's JWT, never sent by the frontend.
"""

import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel


class BidCreateRequest(BaseModel):
    """Fields a Vendor provides to place a bid."""

    auction_id: uuid.UUID
    bid_amount: Decimal


class BidResponse(BaseModel):
    """Bid data returned to the client that placed it (the vendor)."""

    id: uuid.UUID
    auction_id: uuid.UUID
    vendor_company_id: uuid.UUID
    bid_amount: Decimal
    bid_time: datetime

    class Config:
        from_attributes = True


class BidWithVendorResponse(BaseModel):
    """
    Bid data with vendor identity attached — buyer-only view.
    Never expose this schema on any vendor-facing route; vendors must
    never see competitor identity, per the auction rules.
    """

    vendor_company_id: uuid.UUID
    vendor_company_name: str
    bid_amount: Decimal
    bid_time: datetime

    class Config:
        from_attributes = True