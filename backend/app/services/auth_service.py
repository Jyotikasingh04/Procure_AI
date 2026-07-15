"""
Auth Service.

Contains all authentication business logic: registration (Buyer/Vendor)
and login. Routers call these functions and never touch the database
or hashing/token logic directly.
"""

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.Company import Company, CompanyType, VerificationStatus
from app.models.user import User, UserRole
from app.schemas.auth import CompanyRegisterRequest, LoginRequest
from app.core.security import hash_password, verify_password, create_access_token


def _register_company(db: Session, data: CompanyRegisterRequest, company_type: CompanyType) -> User:
    """
    Shared logic for registering a Company plus its first User.
    Used by both register_buyer and register_vendor.
    """
    if db.query(User).filter(User.email == data.email).first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email is already registered.",
        )

    if db.query(Company).filter(Company.gst_number == data.gst_number).first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="GST number is already registered.",
        )

    try:
        company = Company(
            company_name=data.company_name,
            company_type=company_type,
            gst_number=data.gst_number,
            pan_number=data.pan_number,
            cin_number=data.cin_number,
            official_email=data.official_email,
            phone_number=data.phone_number,
            address=data.address,
            city=data.city,
            state=data.state,
            country=data.country,
            pincode=data.pincode,
            verification_status=VerificationStatus.PENDING,
        )
        db.add(company)
        db.flush()  # populates company.id without ending the transaction

        role = UserRole.BUYER if company_type == CompanyType.BUYER else UserRole.VENDOR
        user = User(
            company_id=company.id,
            full_name=data.full_name,
            email=data.email,
            password_hash=hash_password(data.password),
            role=role,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    except Exception:
        db.rollback()
        raise

    return user


def register_buyer(db: Session, data: CompanyRegisterRequest) -> User:
    """Register a new Buyer Company and its first User."""
    return _register_company(db, data, CompanyType.BUYER)


def register_vendor(db: Session, data: CompanyRegisterRequest) -> User:
    """Register a new Vendor Company and its first User."""
    return _register_company(db, data, CompanyType.VENDOR)


def login(db: Session, data: LoginRequest) -> str:
    """
    Verify credentials and return a signed JWT access token.
    """
    user = db.query(User).filter(User.email == data.email).first()

    # Same error for "no such user" and "wrong password" to avoid
    # revealing which one was incorrect.
    if not user or not verify_password(data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Account is inactive.",
        )

    token = create_access_token(
        {
            "sub": str(user.id),
            "role": user.role.value,
            "company_id": str(user.company_id),
        }
    )
    return token