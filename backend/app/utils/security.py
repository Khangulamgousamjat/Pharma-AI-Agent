"""
utils/security.py — Firebase token verification helpers.

Replaced standard JWT validation with Firebase Auth token verification.
"""

from typing import Optional
from firebase_admin import auth
import logging

logger = logging.getLogger(__name__)

# Note: Password hashing is removed because Firebase Auth handles passwords securely natively.
# Note: create_access_token is removed because Firebase Client SDK handles token generation natively.

def verify_token(token: str) -> Optional[dict]:
    """
    Verify a Firebase ID token.

    Args:
        token: Firebase ID token string from Authorization header

    Returns:
        dict: Decoded token claims (including uid, email) if valid, None if invalid
    """
    try:
        decoded_token = auth.verify_id_token(token)
        # Firebase token contains 'uid' and 'email'. We'll map 'uid' to 'sub' for compatibility
        # if other parts of the app expect 'sub' (subject).
        payload = {
            "sub": decoded_token.get("email"), # Legacy compatibility for email
            "user_id": decoded_token.get("uid"),
            "email": decoded_token.get("email"),
            "role": decoded_token.get("role", "user") # Custom claims can hold roles
        }
        return payload
    except Exception as e:
        logger.warning(f"Firebase token verification failed: {e}")
        return None
