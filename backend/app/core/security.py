"""
Security Core.

Provides password hashing/verification and JWT access token
creation/decoding. Pure utility functions only — no request handling,
no database access.
"""

from datetime import datetime, timedelta

from jose import jwt, JWTError
from passlib.context import CryptContext

from app.config.settings import settings

# bcrypt handles salting and hashing work factor internally.
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    """
    Hash a plain-text password. Only the returned hash should ever
    be stored (e.g. in User.password_hash).
    """
    return pwd_context.hash(password)


def verify_password(plain_password: str, password_hash: str) -> bool:
    """
    Check a plain-text password against a stored hash.
    """
    return pwd_context.verify(plain_password, password_hash)


def create_access_token(data: dict) -> str:
    """
    Create a signed JWT access token, embedding an expiry claim based
    on ACCESS_TOKEN_EXPIRE_MINUTES.
    """
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})

    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def decode_access_token(token: str) -> dict | None:
    """
    Decode and verify a JWT access token. Returns the payload if
    valid, or None if the token is invalid or expired.
    """
    try:
        return jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    except JWTError:
        return None