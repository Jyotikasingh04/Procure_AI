"""
Profile Router.

Thin HTTP layer for the read-only profile endpoint. Reuses the same
JWT-to-User dependency pattern already defined in auction.py — no
new authentication logic is introduced here.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.core.security import decode_access_token
from app.database.database import get_db
from app.models.user import User
from app.schemas.profile import ProfileResponse
from app.services import profile_service

router = APIRouter(prefix="/api/profile", tags=["profile"])

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    """
    Decode the JWT, look up the corresponding User, and return it.
    Raises 401 if the token is invalid or the user no longer exists.

    Identical in behavior to the get_current_user dependency in
    auction.py; kept as a local copy for now rather than shared,
    consistent with how auction.py already does it.
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


@router.get("/", response_model=ProfileResponse)
def get_my_profile(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Return the authenticated user's own company, address, and user
    profile. Read-only — no update or delete operations exist here.
    company_id and user_id are never taken from the client; both come
    from current_user, which is derived entirely from the JWT.
    """
    return profile_service.get_my_profile(current_user, db)