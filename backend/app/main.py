"""
FastAPI Application Entry Point.

Creates the FastAPI application instance for ProcureAI, creates tables
(temporary — Alembic migrations will replace this later), and
registers the auth router.
"""

from fastapi import FastAPI

from app.database.database import Base, engine

# Import each model so its table is registered on Base.metadata
# before create_all runs.
import app.models.Company
import app.models.user
import app.models.auction
import app.models.bid
from dotenv import load_dotenv

from app.api.auth import router as auth_router
from app.api.auction import router as auction_router
from app.api.bid import router as bid_router
from app.api.dashboard import router as dashboard_router
from app.api.profile import router as profile_router
from app.api.admin import router as admin_router

# Temporary: creates tables directly, bypassing Alembic for now.
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="ProcureAI",
    description="AI Powered Vendor Procurement Platform",
)

app.include_router(auth_router)
app.include_router(auction_router)
app.include_router(bid_router)
app.include_router(dashboard_router)
app.include_router(profile_router)
app.include_router(admin_router)


@app.get("/")
def read_root():
    """
    Root endpoint. Confirms the API is running.
    """
    return {"message": "Welcome to ProcureAI"}