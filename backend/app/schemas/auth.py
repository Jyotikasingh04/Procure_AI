"""
Auth Schemas.

Pydantic request/response models for registration and login.
company_type is not part of the request body — it's implied by which
endpoint is called (/register/buyer vs /register/vendor) and set by
the service layer.
"""

import uuid

from pydantic import BaseModel, EmailStr


class CompanyRegisterRequest(BaseModel):
    """Shared registration fields for both Buyer and Vendor companies."""

    company_name: str
    gst_number: str
    pan_number: str
    cin_number: str | None = None

    official_email: EmailStr
    phone_number: str

    address: str
    city: str
    state: str
    country: str
    pincode: str

    # First user created for this company (becomes the login account)
    full_name: str
    email: EmailStr
    password: str


class LoginRequest(BaseModel):
    """Login credentials."""

    email: EmailStr
    password: str


class RegisterResponse(BaseModel):
    """Returned after successful registration."""

    company_id: uuid.UUID
    user_id: uuid.UUID
    message: str


class TokenResponse(BaseModel):
    """Returned after successful login."""

    access_token: str
    token_type: str = "bearer"