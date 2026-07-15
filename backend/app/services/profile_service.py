"""
Profile Service.

Read-only business logic for a user viewing their own profile.
Never accepts a company_id or user_id argument from the caller side —
both are always derived from the authenticated User object passed in
by the router, which itself comes from the JWT.
"""

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.Company import Company
from app.models.user import User
from app.schemas.profile import AddressProfile, CompanyProfile, ProfileResponse, UserProfile


def get_my_profile(current_user: User, db: Session) -> ProfileResponse:
    """
    Build the profile response for the currently authenticated user.
    Re-fetches the Company row to guard against it having been
    deleted since the user's token was issued.
    """
    company = db.query(Company).filter(Company.id == current_user.company_id).first()
    if company is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Company not found.",
        )

    return ProfileResponse(
        company=CompanyProfile.from_orm(company),
        address=AddressProfile.from_orm(company),
        user=UserProfile.from_orm(current_user),
    )