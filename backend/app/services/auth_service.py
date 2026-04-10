"""
services/auth_service.py — Business logic for user authentication.

Separates authentication logic from route handlers, keeping routes thin.
"""

from sqlalchemy.orm import Session
from fastapi import HTTPException, status
import logging

from app.models.user import User
from app.schemas.user import UserRegister, UserLogin, UserResponse, TokenResponse
from app.utils.security import hash_password, verify_password, create_access_token

logger = logging.getLogger(__name__)


def register_user(db: Session, data: UserRegister) -> TokenResponse:
    """
    Register a new user account.

    Checks for duplicate email, hashes the password, creates the user,
    and returns a JWT token immediately (auto-login after register).

    Args:
        db: Database session
        data: Registration data (name, email, password)

    Returns:
        TokenResponse: JWT access token + user info

    Raises:
        HTTPException 400: If email is already registered
    """
    # Check if email is already in use
    existing = db.query(User).filter(User.email == data.email).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered. Please use a different email or login.",
        )

    # Block admin registration
    if data.role == "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin registration is not allowed. Please use the pre-defined admin account.",
        )

    # Determine approval status based on role
    # Pharmacists (role='pharmacist') require approval (is_approved=0)
    # Regular users (role='user') are auto-approved (is_approved=1)
    is_approved = 1 if data.role == "user" else 0

    # Hash password before storing — NEVER save plaintext
    user = User(
        name=data.name,
        email=data.email,
        password_hash=hash_password(data.password),
        role=data.role,
        is_approved=is_approved,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    # For pharmacists, don't return a token yet (they need approval)
    if not is_approved:
        return TokenResponse(
            access_token="",
            user=UserResponse.model_validate(user),
        )

    # Generate JWT for immediate authentication for auto-approved users
    token = create_access_token({
        "sub": user.email,
        "user_id": user.id,
        "role": user.role,
    })

    logger.info(f"New user registered: {user.email} (id={user.id}, role={user.role})")
    return TokenResponse(
        access_token=token,
        user=UserResponse.model_validate(user),
    )


def login_user(db: Session, data: UserLogin) -> TokenResponse:
    """
    Authenticate a user with email and password.

    Args:
        db: Database session
        data: Login credentials (email, password)

    Returns:
        TokenResponse: JWT access token + user info

    Raises:
        HTTPException 401: If credentials are invalid
    """
    # Fetch user by email
    user = db.query(User).filter(User.email == data.email).first()

    # Verify credentials — use constant-time comparison via bcrypt
    if not user or not verify_password(data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Check if user is approved (pharmacists require approval)
    if not user.is_approved:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Your account is pending admin approval. Please check back later.",
        )

    # Issue JWT token
    token = create_access_token({
        "sub": user.email,
        "user_id": user.id,
        "role": user.role,
    })

    logger.info(f"User logged in: {user.email} (id={user.id})")
    return TokenResponse(
        access_token=token,
        user=UserResponse.model_validate(user),
    )


def get_current_user_from_token(db: Session, token: str) -> User:
    """
    Resolve a JWT token to a User object.

    Used as a FastAPI dependency in protected routes.

    Args:
        db: Database session
        token: JWT access token string

    Returns:
        User: Authenticated user

    Raises:
        HTTPException 401: If token is invalid or user not found
    """
    from app.utils.security import verify_token

    payload = verify_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = db.query(User).filter(User.email == payload.get("sub")).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found.",
        )
    return user
