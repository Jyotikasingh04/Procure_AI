"""
Profile Schemas.

Pydantic response models for the read-only profile endpoint.
There is no request schema — the endpoint takes no input beyond the
JWT, which never accepts a company_id or user_id from the client.
"""

from app.models.Company import CompanyType, VerificationStatus
from app.models.user import UserRole
from pydantic import BaseModel


class CompanyProfile(BaseModel):
    """Company-level fields shown on the profile page."""

    company_name: str
    company_type: CompanyType
    gst_number: str
    pan_number: str
    cin_number: str | None
    official_email: str
    phone_number: str
    verification_status: VerificationStatus

    class Config:
        from_attributes = True


class AddressProfile(BaseModel):
    """Address fields, kept separate from CompanyProfile per the requested response shape."""

    address: str
    city: str
    state: str
    country: str
    pincode: str

    class Config:
        from_attributes = True


class UserProfile(BaseModel):
    """User-level fields shown on the profile page."""

    full_name: str
    email: str
    role: UserRole

    class Config:
        from_attributes = True


class ProfileResponse(BaseModel):
    """Full profile payload: the logged-in user's own company, address, and user info."""

    company: CompanyProfile
    address: AddressProfile
    user: UserProfile