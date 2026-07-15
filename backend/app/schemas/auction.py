"""
Auction Schemas.

Pydantic request/response models for auction creation.
buyer_company_id is intentionally NOT part of the request — it is
derived from the authenticated user's JWT, never sent by the frontend.
"""

import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel

from app.models.auction import AuctionStatus


class AuctionCreateRequest(BaseModel):
    """Fields a Buyer provides to create an auction."""

    title: str
    description: str
    material_name: str
    quantity: int
    unit: str
    base_price: Decimal
    start_time: datetime
    end_time: datetime


class AuctionResponse(BaseModel):
    """Auction data returned to the client."""

    id: uuid.UUID
    buyer_company_id: uuid.UUID
    title: str
    description: str
    material_name: str
    quantity: int
    unit: str
    base_price: Decimal
    start_time: datetime
    end_time: datetime
    status: AuctionStatus
    winner_company_id: uuid.UUID | None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class AwardAuctionRequest(BaseModel):
    """Fields a Buyer provides to award an ENDED auction."""

    winner_company_id: uuid.UUID