"""
Auction Service.

Contains auction business logic. Routers call these functions and
never construct Auction rows or touch the database directly.
"""

import logging
import uuid
from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.auction import Auction, AuctionStatus
from app.models.bid import Bid
from app.models.Company import Company, CompanyType, VerificationStatus
from app.schemas.auction import AuctionCreateRequest
from app.services import gemini_service
from app.services import email_service

logger = logging.getLogger(__name__)


def create_auction(db: Session, data: AuctionCreateRequest, buyer_company_id: uuid.UUID) -> Auction:
    """
    Create a new auction owned by the given buyer company.

    buyer_company_id must come from the authenticated user's JWT,
    never from the request body, so a buyer can never create an
    auction under another company's name.
    """
    auction = Auction(
        buyer_company_id=buyer_company_id,
        title=data.title,
        description=data.description,
        material_name=data.material_name,
        quantity=data.quantity,
        unit=data.unit,
        base_price=data.base_price,
        start_time=data.start_time,
        end_time=data.end_time,
        status=AuctionStatus.DRAFT,
        winner_company_id=None,
    )

    try:
        db.add(auction)
        db.commit()
        db.refresh(auction)
    except Exception:
        db.rollback()
        raise

    return auction


def _remaining_time_seconds(auction: Auction) -> int:
    end_time = auction.end_time
    if end_time.tzinfo is None:
        end_time = end_time.replace(tzinfo=timezone.utc)
    now = datetime.now(timezone.utc)
    return max(int((end_time - now).total_seconds()), 0)


def get_live_auctions(db: Session) -> list[dict]:
    """
    Return all LIVE auctions for vendors to browse, sorted by
    end_time ascending. Excludes buyer/winner company identifiers and
    all bid information — vendors only see what's needed to decide
    whether to bid.
    """
    auctions = (
        db.query(Auction)
        .filter(Auction.status == AuctionStatus.LIVE)
        .order_by(Auction.end_time.asc())
        .all()
    )

    return [
        {
            "id": a.id,
            "title": a.title,
            "description": a.description,
            "material_name": a.material_name,
            "quantity": a.quantity,
            "unit": a.unit,
            "base_price": a.base_price,
            "start_time": a.start_time,
            "end_time": a.end_time,
            "status": a.status,
            "remaining_time_seconds": _remaining_time_seconds(a),
        }
        for a in auctions
    ]


def start_auction(db: Session, auction_id: uuid.UUID, buyer_company_id: uuid.UUID) -> Auction:
    """
    Move an auction from DRAFT to LIVE. Only the buyer company that
    created the auction may start it, and only while it's still DRAFT.
    start_time, end_time, and winner_company_id are never touched here.

    After the transition commits, every APPROVED vendor company is
    emailed a live-auction notification. Email delivery failures are
    logged and swallowed — they must never affect the already-committed
    auction state transition.
    """
    auction = db.query(Auction).filter(Auction.id == auction_id).first()
    if auction is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Auction not found.",
        )

    if auction.buyer_company_id != buyer_company_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not own this auction.",
        )

    if auction.status != AuctionStatus.DRAFT:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only a DRAFT auction can be started.",
        )

    auction.status = AuctionStatus.LIVE

    try:
        db.commit()
        db.refresh(auction)
    except Exception:
        db.rollback()
        raise

    approved_vendors = (
        db.query(Company)
        .filter(Company.company_type == CompanyType.VENDOR)
        .filter(Company.verification_status == VerificationStatus.APPROVED)
        .all()
    )

    for vendor_company in approved_vendors:
        try:
            email_service.send_auction_live_email(
                recipient_email=vendor_company.official_email,
                company_name=vendor_company.company_name,
                auction_title=auction.title,
                material_name=auction.material_name,
                quantity=auction.quantity,
                unit=auction.unit,
            )
        except Exception:
            logger.exception(
                "Failed to send auction-live email to vendor company %s for auction %s.",
                vendor_company.id,
                auction.id,
            )

    return auction


def end_auction(db: Session, auction_id: uuid.UUID, buyer_company_id: uuid.UUID) -> Auction:
    """
    Move an auction from LIVE to ENDED. Only the buyer company that
    created the auction may end it, and only while it's still LIVE.
    winner_company_id remains NULL — awarding is a separate step.
    """
    auction = db.query(Auction).filter(Auction.id == auction_id).first()
    if auction is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Auction not found.",
        )

    if auction.buyer_company_id != buyer_company_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not own this auction.",
        )

    if auction.status != AuctionStatus.LIVE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only a LIVE auction can be ended.",
        )

    auction.status = AuctionStatus.ENDED

    try:
        db.commit()
        db.refresh(auction)
    except Exception:
        db.rollback()
        raise

    return auction


def award_auction(
    db: Session,
    auction_id: uuid.UUID,
    buyer_company_id: uuid.UUID,
    winner_company_id: uuid.UUID,
) -> Auction:
    """
    Manually award an ENDED auction to a vendor who actually bid on it.
    The buyer, not AI, selects the winner — the lowest bid is not
    validated here as "correct", only that the chosen winner is a
    legitimate bidder on this auction.

    After the award commits, the winning vendor is emailed a
    congratulations notification. Email delivery failures are logged
    and swallowed — they must never affect the already-committed award.
    """
    auction = db.query(Auction).filter(Auction.id == auction_id).first()
    if auction is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Auction not found.",
        )

    if auction.buyer_company_id != buyer_company_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not own this auction.",
        )

    if auction.status != AuctionStatus.ENDED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only an ENDED auction can be awarded.",
        )

    bids = db.query(Bid).filter(Bid.auction_id == auction_id).all()
    if not bids:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot award an auction with no bids.",
        )

    if not any(b.vendor_company_id == winner_company_id for b in bids):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Selected winner did not place a bid on this auction.",
        )

    auction.winner_company_id = winner_company_id
    auction.status = AuctionStatus.AWARDED

    try:
        db.commit()
        db.refresh(auction)
    except Exception:
        db.rollback()
        raise

    winner_company = db.query(Company).filter(Company.id == winner_company_id).first()
    if winner_company is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Winning company not found.",
        )

    try:
        email_service.send_award_email(
            recipient_email=winner_company.official_email,
            company_name=winner_company.company_name,
            auction_title=auction.title,
        )
    except Exception:
        logger.exception(
            "Failed to send award email to winning vendor company %s for auction %s.",
            winner_company.id,
            auction.id,
        )

    return auction


def get_buyer_auctions(db: Session, buyer_company_id: uuid.UUID) -> list[dict]:
    """
    Return all auctions created by the given buyer company, newest
    first. buyer_company_id must come from the authenticated user's
    JWT, never from a query parameter, so a buyer can only ever see
    their own company's auctions.
    """
    auctions = (
        db.query(Auction)
        .filter(Auction.buyer_company_id == buyer_company_id)
        .order_by(Auction.created_at.desc())
        .all()
    )

    return [
        {
            "id": a.id,
            "title": a.title,
            "material_name": a.material_name,
            "quantity": a.quantity,
            "unit": a.unit,
            "base_price": a.base_price,
            "status": a.status,
            "start_time": a.start_time,
            "end_time": a.end_time,
            "created_at": a.created_at,
        }
        for a in auctions
    ]


def get_auction_bids(db: Session, auction_id: uuid.UUID, buyer_company_id: uuid.UUID) -> list[dict]:
    """
    Return every bid placed on an auction, lowest bid_amount first,
    with the vendor company identified. Buyer-only — vendors must
    never reach this function, since it exposes competitor identity.
    """
    auction = db.query(Auction).filter(Auction.id == auction_id).first()
    if auction is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Auction not found.",
        )

    if auction.buyer_company_id != buyer_company_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not own this auction.",
        )

    rows = (
        db.query(Bid, Company.company_name)
        .join(Company, Company.id == Bid.vendor_company_id)
        .filter(Bid.auction_id == auction_id)
        .order_by(Bid.bid_amount.asc())
        .all()
    )

    return [
        {
            "vendor_company_id": bid.vendor_company_id,
            "vendor_company_name": name,
            "bid_amount": bid.bid_amount,
            "bid_time": bid.bid_time,
        }
        for bid, name in rows
    ]


def get_auction_summary(db: Session, auction_id: uuid.UUID, buyer_company_id: uuid.UUID) -> dict:
    """
    Generate an AI procurement summary for an auction. Only the buyer
    company that owns the auction may request it. Available for ENDED
    or AWARDED auctions only — summarizing a still-LIVE auction would
    describe an incomplete, still-changing bid set.

    Vendor identities are intentionally excluded from what's passed to
    Gemini; only bid amounts feed the summary, so the AI has no way to
    reference, imply, or favor a specific vendor.

    Returns the response payload directly, e.g. {"summary": "..."}.
    """
    auction = db.query(Auction).filter(Auction.id == auction_id).first()
    if auction is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Auction not found.",
        )

    if auction.buyer_company_id != buyer_company_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not own this auction.",
        )

    if auction.status not in (AuctionStatus.ENDED, AuctionStatus.AWARDED):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="AI summary is only available once an auction has ENDED or been AWARDED.",
        )

    bids = db.query(Bid).filter(Bid.auction_id == auction_id).all()
    bid_amounts = [b.bid_amount for b in bids]

    if not bid_amounts:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="AI summary is unavailable because no bids were placed.",
        )

    duration = auction.end_time - auction.start_time
    total_seconds = int(duration.total_seconds())
    hours, remainder = divmod(total_seconds, 3600)
    minutes, _ = divmod(remainder, 60)
    duration_display = f"{hours}h {minutes}m"

    summary = gemini_service.generate_auction_summary(
        auction_title=auction.title,
        material_name=auction.material_name,
        quantity=auction.quantity,
        unit=auction.unit,
        base_price=auction.base_price,
        duration_display=duration_display,
        bid_amounts=bid_amounts,
    )

    return {"summary": summary}