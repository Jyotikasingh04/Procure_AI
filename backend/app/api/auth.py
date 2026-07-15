"""
Auth Router.

Thin HTTP layer for registration and login. All business logic lives
in auth_service.py — this file only parses requests, calls the
service, and shapes responses.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.schemas.auth import (
    CompanyRegisterRequest,
    LoginRequest,
    RegisterResponse,
    TokenResponse,
)
from app.services import auth_service

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/register/buyer", response_model=RegisterResponse)
def register_buyer(data: CompanyRegisterRequest, db: Session = Depends(get_db)):
    """Register a new Buyer Company and its first User."""
    user = auth_service.register_buyer(db, data)
    return RegisterResponse(
        company_id=user.company_id,
        user_id=user.id,
        message="Buyer registered successfully. Pending admin verification.",
    )


@router.post("/register/vendor", response_model=RegisterResponse)
def register_vendor(data: CompanyRegisterRequest, db: Session = Depends(get_db)):
    """Register a new Vendor Company and its first User."""
    user = auth_service.register_vendor(db, data)
    return RegisterResponse(
        company_id=user.company_id,
        user_id=user.id,
        message="Vendor registered successfully. Pending admin verification.",
    )


@router.post("/login", response_model=TokenResponse)
def login(data: LoginRequest, db: Session = Depends(get_db)):
    """Verify credentials and return a JWT access token."""
    token = auth_service.login(db, data)
    return TokenResponse(access_token=token)