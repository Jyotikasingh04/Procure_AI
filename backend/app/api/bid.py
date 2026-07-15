"""
Bid Router.

Thin HTTP layer for placing bids. Business logic lives in
bid_service.py. get_current_user is duplicated here from auction.py
since no shared dependency file exists yet — worth consolidating into
app/core/dependencies.py later.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.core.security import decode_access_token
from app.models.user import User, UserRole
from app.schemas.bid import BidCreateRequest, BidResponse
from app.services import bid_service

router = APIRouter(prefix="/api/bid", tags=["bid"])

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


@router.post("/", response_model=BidResponse)
def place_bid(
    data: BidCreateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Place a bid on a LIVE auction. Only VENDOR users are allowed."""
    if current_user.role != UserRole.VENDOR:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only vendor users can place bids.",
        )

    return bid_service.place_bid(
        db, data, vendor_company_id=current_user.company_id
    )