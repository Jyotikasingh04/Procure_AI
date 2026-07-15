"""
Dashboard Service.

Computes live buyer and vendor dashboard views for a reverse auction.
Rank, remaining time, and bid aggregates are all calculated fresh on
every call from Bid rows — nothing is cached or stored in the database.
"""

import uuid
from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.auction import Auction
from app.models.bid import Bid


def _get_auction_or_404(db: Session, auction_id: uuid.UUID) -> Auction:
    auction = db.query(Auction).filter(Auction.id == auction_id).first()
    if auction is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Auction not found.",
        )
    return auction


def _remaining_time_seconds(auction: Auction) -> int:
    end_time = auction.end_time
    if end_time.tzinfo is None:
        end_time = end_time.replace(tzinfo=timezone.utc)
    now = datetime.now(timezone.utc)
    return max(int((end_time - now).total_seconds()), 0)


def get_buyer_dashboard(db: Session, auction_id: uuid.UUID, buyer_company_id: uuid.UUID) -> dict:
    """
    Full bid visibility for the buyer who owns this auction.
    """
    auction = _get_auction_or_404(db, auction_id)

    if auction.buyer_company_id != buyer_company_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not own this auction.",
        )

    bids = db.query(Bid).filter(Bid.auction_id == auction_id).all()

    total_bids = len(bids)
    total_unique_vendors = len({b.vendor_company_id for b in bids})

    lowest_bid = None
    latest_bid_time = None

    if bids:
        lowest_bid = min(b.bid_amount for b in bids)
        latest_bid_time = max(b.bid_time for b in bids)

    return {
        "auction_id": auction.id,
        "auction_title": auction.title,
        "auction_status": auction.status,
        "remaining_time_seconds": _remaining_time_seconds(auction),
        "total_bids": total_bids,
        "total_unique_vendors": total_unique_vendors,
        "lowest_bid": lowest_bid,
        "latest_bid_time": latest_bid_time,
    }


def get_vendor_dashboard(db: Session, auction_id: uuid.UUID, vendor_company_id: uuid.UUID) -> dict:
    """
    Restricted view for a vendor: only their own rank and bid, never
    other vendors' identities, bids, or the lowest bid amount.
    """
    auction = _get_auction_or_404(db, auction_id)

    bids = db.query(Bid).filter(Bid.auction_id == auction_id).all()

    # Each vendor's best (lowest) bid, sorted ascending -> rank order.
    best_per_vendor: dict[uuid.UUID, Bid] = {}
    for b in bids:
        current_best = best_per_vendor.get(b.vendor_company_id)
        if current_best is None or (b.bid_amount, b.bid_time) < (current_best.bid_amount, current_best.bid_time):
            best_per_vendor[b.vendor_company_id] = b

    ranked_vendor_ids = [
        vendor_id
        for vendor_id, _ in sorted(
            best_per_vendor.items(), key=lambda item: (item[1].bid_amount, item[1].bid_time)
        )
    ]

    your_rank = None
    if vendor_company_id in ranked_vendor_ids:
        your_rank = ranked_vendor_ids.index(vendor_company_id) + 1

    your_bids = [b for b in bids if b.vendor_company_id == vendor_company_id]
    your_latest_bid = max(your_bids, key=lambda b: b.bid_time).bid_amount if your_bids else None

    return {
        "auction_id": auction.id,
        "auction_title": auction.title,
        "auction_status": auction.status,
        "remaining_time_seconds": _remaining_time_seconds(auction),
        "your_latest_bid": your_latest_bid,
        "your_rank": your_rank,
        "total_bidders": len(best_per_vendor),
    }