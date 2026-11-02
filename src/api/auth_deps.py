"""Authentication Dependencies for FastAPI Bridge (Phase 7).

Extracts and validates signed session tokens from either:
1. HTTP-only secure cookie ('session_token')
2. Authorization header ('Bearer <token>')
"""

import logging
from typing import Optional
from fastapi import Request, HTTPException, status
from src.database.models import User
from src.services.auth_service import get_authenticated_user_from_token

logger = logging.getLogger("pricewise.auth_deps")


def extract_token_from_request(request: Request) -> Optional[str]:
    """Extract session token from Authorization header or cookie."""
    # 1. Check Authorization Bearer header first (explicit request header takes precedence)
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        return auth_header[7:].strip()

    # 2. Check HTTP-only cookie
    cookie_token = request.cookies.get("session_token")
    if cookie_token:
        return cookie_token

    return None


def get_current_user(request: Request) -> User:
    """
    FastAPI dependency requiring valid authenticated user.
    Raises HTTP 401 Unauthorized if token is missing, invalid, or expired.
    """
    token = extract_token_from_request(request)
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required. Please sign in to your account.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = get_authenticated_user_from_token(token)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session has expired or credentials are invalid. Please log in again.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user


def get_optional_current_user(request: Request) -> Optional[User]:
    """
    FastAPI dependency that returns authenticated User if logged in,
    or None if browsing anonymously.
    """
    token = extract_token_from_request(request)
    if not token:
        return None

    return get_authenticated_user_from_token(token)
