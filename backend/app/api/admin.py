"""
Admin Router.

Thin HTTP layer for platform admin endpoints: dashboard metrics,
listing companies by verification status, and approving/rejecting
registrations. Reuses the same JWT-to-User dependency pattern already
used in auction.py and profile.py — no new authentication logic.
Every route requires UserRole.ADMIN.
"""

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.core.security import decode_access_token
from app.database.database import get_db
from app.models.Company import VerificationStatus
from app.models.user import User, UserRole
from app.schemas.admin import AdminCompanyResponse, AdminDashboardResponse
from app.services import admin_service

router = APIRouter(prefix="/api/admin", tags=["admin"])

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    """
    Decode the JWT, look up the corresponding User, and return it.
    Raises 401 if the token is invalid or the user no longer exists.

    Identical in behavior to the get_current_user dependency already
    used in auction.py and profile.py; kept as a local copy for now,
    consistent with how those routers already do it.
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


def _require_admin(current_user: User) -> None:
    """Raise 403 unless the current user is a platform admin."""
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admin users can access this endpoint.",
        )


@router.get("/dashboard", response_model=AdminDashboardResponse)
def get_dashboard(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Return platform-wide summary counts: pending/approved companies,
    total buyers, total vendors, total auctions.
    """
    _require_admin(current_user)
    return admin_service.get_dashboard(db)


@router.get("/companies", response_model=list[AdminCompanyResponse])
def get_companies(
    status_filter: VerificationStatus = Query(..., alias="status"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    List all companies with the given verification status
    (?status=pending or ?status=approved), newest first.
    """
    _require_admin(current_user)
    return admin_service.get_companies_by_status(db, status_filter)


@router.patch("/companies/{company_id}/approve", response_model=AdminCompanyResponse)
def approve_company(
    company_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Approve a PENDING company's registration. Only changes
    verification_status — company_type and user roles are untouched.
    """
    _require_admin(current_user)
    return admin_service.approve_company(db, company_id)


@router.patch("/companies/{company_id}/reject", response_model=AdminCompanyResponse)
def reject_company(
    company_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Reject a PENDING company's registration. Only changes
    verification_status — company_type and user roles are untouched.
    """
    _require_admin(current_user)
    return admin_service.reject_company(db, company_id)