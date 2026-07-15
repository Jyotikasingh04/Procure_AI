"""
Shared Declarative Base.

Re-exports Base from database.py so that all ORM models can import it
from a single, stable location.
"""

from app.database.database import Base

__all__ = ["Base"]