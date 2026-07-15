"""
Admin Schemas.

Pydantic response models for the admin dashboard and company
moderation endpoints. All read-only except the approve/reject
actions, which only ever change verification_status — never role,
never company_type.
"""

import uuid
from datetime import datetime

from pydantic import BaseModel

from app.models.Company import CompanyType, VerificationStatus


class AdminDashboardResponse(BaseModel):
    """Summary counts shown on the admin dashboard."""

    pending_companies: int
    approved_companies: int
    total_buyers: int
    total_vendors: int
    total_auctions: int


class AdminCompanyResponse(BaseModel):
    """A single company row shown in the admin company list."""

    id: uuid.UUID
    company_name: str
    company_type: CompanyType
    gst_number: str
    pan_number: str
    cin_number: str | None
    official_email: str
    phone_number: str
    address: str
    city: str
    state: str
    country: str
    pincode: str
    verification_status: VerificationStatus
    created_at: datetime

    class Config:
        from_attributes = True