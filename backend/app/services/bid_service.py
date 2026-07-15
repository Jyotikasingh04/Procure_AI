"""
Bid Service.

Contains bid placement business logic: auction existence, LIVE status,
and price validation against the current lowest bid (or base_price if
no bids exist yet). Routers call these functions and never touch the
database directly.
"""

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.auction import Auction, AuctionStatus
from app.models.bid import Bid
from app.schemas.bid import BidCreateRequest


def place_bid(db: Session, data: BidCreateRequest, vendor_company_id) -> Bid:
    """
    Validate and insert a new bid for the given auction.
    """
    auction = db.query(Auction).filter(Auction.id == data.auction_id).first()
    if auction is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Auction not found.",
        )

    if auction.status != AuctionStatus.LIVE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Bids can only be placed on a LIVE auction.",
        )

    # Current lowest bid so far, if any.
    lowest_bid = (
        db.query(Bid)
        .filter(Bid.auction_id == auction.id)
        .order_by(Bid.bid_amount.asc())
        .first()
    )

    ceiling = lowest_bid.bid_amount if lowest_bid else auction.base_price

    if data.bid_amount >= ceiling:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Bid amount must be lower than {ceiling}.",
        )

    bid = Bid(
        auction_id=auction.id,
        vendor_company_id=vendor_company_id,
        bid_amount=data.bid_amount,
    )

    try:
        db.add(bid)
        db.commit()
        db.refresh(bid)
    except Exception:
        db.rollback()
        raise

    return bid