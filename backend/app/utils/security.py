"""
utils/security.py — JWT token creation and verification helpers.

Handles all cryptographic operations for authentication:
- Password hashing with bcrypt (never store plaintext passwords)
- JWT token generation and validation
"""

from datetime import datetime, timedelta, timezone
from typing import Optional
from jose import JWTError, jwt
import bcrypt
import logging

from app.config import settings

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Password Hashing
# ---------------------------------------------------------------------------

def hash_password(password: str) -> str:
    """
    Hash a plaintext password using bcrypt.

    bcrypt automatically generates a salt and includes it in the hash,
    making each hash unique even for the same password.

    Args:
        password: Plaintext password string

    Returns:
        str: bcrypt hashed password string
    """
    salt = bcrypt.gensalt(rounds=12)  # 12 rounds = good security/speed balance
    hashed = bcrypt.hashpw(password.encode("utf-8"), salt)
    return hashed.decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a plaintext password against a bcrypt hash.

    Args:
        plain_password: Password provided by the user at login
        hashed_password: bcrypt hash stored in the database

    Returns:
        bool: True if password matches, False otherwise
    """
    return bcrypt.checkpw(
        plain_password.encode("utf-8"),
        hashed_password.encode("utf-8"),
    )


# ---------------------------------------------------------------------------
# JWT Tokens
# ---------------------------------------------------------------------------

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Create a signed JWT access token.

    The token contains user claims (sub = user email, role, user_id) and
    an expiry timestamp. It is signed with the JWT_SECRET key.

    Args:
        data: Dictionary of claims to encode (e.g., {"sub": email, "role": "user"})
        expires_delta: Optional custom expiration duration

    Returns:
        str: Encoded JWT token string
    """
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=settings.jwt_expire_minutes)
    )
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def verify_token(token: str) -> Optional[dict]:
    """
    Decode and verify a JWT token.

    Args:
        token: JWT token string from Authorization header

    Returns:
        dict: Decoded claims if valid, None if expired/invalid
    """
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret,
            algorithms=[settings.jwt_algorithm],
        )
        return payload
    except JWTError as e:
        logger.warning(f"JWT verification failed: {e}")
        return None
