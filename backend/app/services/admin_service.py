"""
Admin Service.

Business logic for the Platform Admin: dashboard metrics, listing
companies by verification status, and approving/rejecting company
registrations. Approval/rejection only ever changes
Company.verification_status — company_type and User.role are never
touched here.
"""

import uuid

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.Company import Company, CompanyType, VerificationStatus
from app.models.auction import Auction


def get_dashboard(db: Session) -> dict:
    """
    Return platform-wide summary counts for the admin dashboard.
    """
    pending_companies = (
        db.query(Company)
        .filter(Company.verification_status == VerificationStatus.PENDING)
        .count()
    )
    approved_companies = (
        db.query(Company)
        .filter(Company.verification_status == VerificationStatus.APPROVED)
        .count()
    )
    total_buyers = (
        db.query(Company)
        .filter(Company.company_type == CompanyType.BUYER)
        .count()
    )
    total_vendors = (
        db.query(Company)
        .filter(Company.company_type == CompanyType.VENDOR)
        .count()
    )
    total_auctions = db.query(Auction).count()

    return {
        "pending_companies": pending_companies,
        "approved_companies": approved_companies,
        "total_buyers": total_buyers,
        "total_vendors": total_vendors,
        "total_auctions": total_auctions,
    }


def get_companies_by_status(db: Session, verification_status: VerificationStatus) -> list[Company]:
    """
    Return all companies with the given verification status, newest
    registrations first. Works for PENDING, APPROVED, and REJECTED
    since verification_status is passed straight through from the
    VerificationStatus enum with no branching.
    """
    return (
        db.query(Company)
        .filter(Company.verification_status == verification_status)
        .order_by(Company.created_at.desc())
        .all()
    )


def approve_company(db: Session, company_id: uuid.UUID) -> Company:
    """
    Approve a company's registration. Only companies currently
    PENDING may be approved — an already-APPROVED or REJECTED company
    must not be silently re-approved.
    """
    company = db.query(Company).filter(Company.id == company_id).first()
    if company is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Company not found.",
        )

    if company.verification_status != VerificationStatus.PENDING:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only a PENDING company can be approved.",
        )

    company.verification_status = VerificationStatus.APPROVED

    try:
        db.commit()
        db.refresh(company)
    except Exception:
        db.rollback()
        raise

    return company


def reject_company(db: Session, company_id: uuid.UUID) -> Company:
    """
    Reject a company's registration. Only companies currently PENDING
    may be rejected.
    """
    company = db.query(Company).filter(Company.id == company_id).first()
    if company is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Company not found.",
        )

    if company.verification_status != VerificationStatus.PENDING:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only a PENDING company can be rejected.",
        )

    company.verification_status = VerificationStatus.REJECTED

    try:
        db.commit()
        db.refresh(company)
    except Exception:
        db.rollback()
        raise

    return company