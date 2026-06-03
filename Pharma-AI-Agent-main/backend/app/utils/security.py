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
    Decode and verify a JWT token. Supports Firebase ID tokens and custom JWT fallback.

    Args:
        token: JWT token string from Authorization header

    Returns:
        dict: Decoded claims if valid, None if expired/invalid
    """
    # 1. Try to verify using Firebase Admin SDK first
    try:
        import firebase_admin
        from firebase_admin import auth as firebase_auth
        import os

        # Check if firebase_admin is initialized
        if not firebase_admin._apps:
            # Try to load credentials from FIREBASE_CREDENTIALS env variable first
            firebase_creds_json = os.environ.get("FIREBASE_CREDENTIALS")
            cred = None
            if firebase_creds_json:
                try:
                    import json
                    creds_dict = json.loads(firebase_creds_json)
                    cred = firebase_admin.credentials.Certificate(creds_dict)
                    logger.info("[Firebase Admin] Initialized from FIREBASE_CREDENTIALS env var.")
                except Exception as ex:
                    logger.error(f"[Firebase Admin] Failed to parse FIREBASE_CREDENTIALS JSON: {ex}")

            if cred:
                firebase_admin.initialize_app(cred, {"storageBucket": settings.firebase_storage_bucket})
            else:
                cred_path = settings.firebase_credentials_json
                if os.path.exists(cred_path):
                    cred = firebase_admin.credentials.Certificate(cred_path)
                    firebase_admin.initialize_app(cred, {"storageBucket": settings.firebase_storage_bucket})
                else:
                    try:
                        # In production (e.g. Render), default credentials might be used
                        firebase_admin.initialize_app()
                    except Exception:
                        pass

        if firebase_admin._apps:
            decoded_token = firebase_auth.verify_id_token(token)
            email = decoded_token.get("email")
            role = "user"
            if email == "admin@gmail.com":
                role = "admin"
            elif email == "pharmacist@pharmaagent.com":
                role = "pharmacist"
            return {
                "sub": email,
                "user_id": decoded_token.get("uid"),
                "role": role,
            }
    except Exception as e:
        logger.debug(f"Firebase token verification failed or skipped: {e}")

    # 2. Fallback to custom JWT decoding
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
