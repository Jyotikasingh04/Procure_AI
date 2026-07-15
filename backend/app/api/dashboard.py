"""
Dashboard Router.

Thin HTTP layer for the live buyer/vendor auction dashboards. Business
logic lives in dashboard_service.py. get_current_user is duplicated
here from auction.py/bid.py since no shared dependency file exists
yet — worth consolidating into app/core/dependencies.py later.
"""

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.core.security import decode_access_token
from app.models.user import User, UserRole
from app.services import dashboard_service

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])

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


@router.get("/buyer/{auction_id}")
def buyer_dashboard(
    auction_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Full bid visibility for the buyer who owns this auction."""
    if current_user.role != UserRole.BUYER:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only buyer users can view this dashboard.",
        )

    return dashboard_service.get_buyer_dashboard(
        db, auction_id, buyer_company_id=current_user.company_id
    )


@router.get("/vendor/{auction_id}")
def vendor_dashboard(
    auction_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Restricted view for a vendor: own rank and bid only."""
    if current_user.role != UserRole.VENDOR:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only vendor users can view this dashboard.",
        )

    return dashboard_service.get_vendor_dashboard(
        db, auction_id, vendor_company_id=current_user.company_id
    )