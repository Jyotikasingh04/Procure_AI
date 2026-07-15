"""
Auction Router.

Thin HTTP layer for auction lifecycle endpoints. Business logic lives
in auction_service.py. This file also defines get_current_user, a local
JWT-to-User dependency (belongs in a shared app/core/dependencies.py
eventually, kept here for now to avoid adding an extra file).
"""

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.core.security import decode_access_token
from app.models.user import User, UserRole
from app.schemas.auction import AuctionCreateRequest, AuctionResponse, AwardAuctionRequest
from app.schemas.bid import BidWithVendorResponse
from app.services import auction_service

router = APIRouter(prefix="/api/auction", tags=["auction"])

# Reads the "Authorization: Bearer <token>" header for us.
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    """
    Decode the JWT, look up the corresponding User, and return it.
    Raises 401 if the token is invalid or the user no longer exists.
    """
    payload = decode_access_token(token)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token.",
        )

    user = db.query(User).filter(User.id == payload.get("sub")).first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found.",
        )

    return user


@router.post("/", response_model=AuctionResponse)
def create_auction(
    data: AuctionCreateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Create a new auction. Only BUYER users are allowed."""
    if current_user.role != UserRole.BUYER:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only buyer users can create auctions.",
        )

    return auction_service.create_auction(
        db, data, buyer_company_id=current_user.company_id
    )


@router.get("/live")
def get_live_auctions(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    List all LIVE auctions for vendors to browse. Only VENDOR users
    are allowed. No buyer/winner identifiers or bid data are exposed.

    Note: this static "/live" path must stay registered before any
    "/{auction_id}" route below, or FastAPI will try to parse "live"
    as a UUID and fail.
    """
    if current_user.role != UserRole.VENDOR:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only vendor users can view live auctions.",
        )

    return auction_service.get_live_auctions(db)


@router.get("/")
def get_buyer_auctions(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    List all auctions created by the authenticated buyer's company,
    newest first. Only BUYER users are allowed. buyer_company_id
    always comes from the JWT, never a query parameter.
    """
    if current_user.role != UserRole.BUYER:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only buyer users can view their auctions.",
        )

    return auction_service.get_buyer_auctions(db, buyer_company_id=current_user.company_id)


@router.patch("/{auction_id}/start", response_model=AuctionResponse)
def start_auction(
    auction_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Move an auction from DRAFT to LIVE. Only BUYER users are allowed,
    and only for auctions their own company created.

    Note: registered after the static "/live" route above, since this
    is a path-parameter route and FastAPI matches routes in order.
    """
    if current_user.role != UserRole.BUYER:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only buyer users can start auctions.",
        )

    return auction_service.start_auction(
        db, auction_id, buyer_company_id=current_user.company_id
    )


@router.patch("/{auction_id}/end", response_model=AuctionResponse)
def end_auction(
    auction_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Move an auction from LIVE to ENDED. Only BUYER users are allowed,
    and only for auctions their own company created.
    """
    if current_user.role != UserRole.BUYER:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only buyer users can end auctions.",
        )

    return auction_service.end_auction(
        db, auction_id, buyer_company_id=current_user.company_id
    )


@router.patch("/{auction_id}/award", response_model=AuctionResponse)
def award_auction(
    auction_id: uuid.UUID,
    data: AwardAuctionRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Manually award an ENDED auction to a vendor who bid on it. Only
    BUYER users are allowed, and only for auctions their own company
    created. AI never selects the winner — this only records the
    buyer's decision.
    """
    if current_user.role != UserRole.BUYER:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only buyer users can award auctions.",
        )

    return auction_service.award_auction(
        db,
        auction_id,
        buyer_company_id=current_user.company_id,
        winner_company_id=data.winner_company_id,
    )


@router.get("/{auction_id}/bids", response_model=list[BidWithVendorResponse])
def get_auction_bids(
    auction_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    List every bid on an auction, vendor identity included. Only
    BUYER users are allowed, and only for auctions their own company
    created — this is the one place vendor identity is exposed, so
    it must never be reachable by a VENDOR-role user.
    """
    if current_user.role != UserRole.BUYER:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only buyer users can view auction bids.",
        )

    return auction_service.get_auction_bids(
        db, auction_id, buyer_company_id=current_user.company_id
    )
@router.get("/{auction_id}/summary")
def get_auction_summary(
    auction_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Generate and return an AI procurement summary for an ENDED or
    AWARDED auction. Only BUYER users are allowed, and only for
    auctions their own company created. The AI never selects a
    winner or recommends a vendor — see gemini_service for the
    constraints enforced on the generated text itself.
    """
    if current_user.role != UserRole.BUYER:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only buyer users can view the AI summary.",
        )

    return auction_service.get_auction_summary(
        db,
        auction_id,
        buyer_company_id=current_user.company_id,
    )