"""
services/auth_service.py — Business logic for user authentication.

Updated for Firebase Migration.
"""

from fastapi import HTTPException, status
import logging
from firebase_admin import firestore
from typing import Any

from app.models.user import User
from app.schemas.user import UserRegister, UserResponse, TokenResponse
from app.utils.security import verify_token

logger = logging.getLogger(__name__)


def register_user(db: firestore.Client, data: UserRegister) -> UserResponse:
    """
    Register a new user account profile in Firestore.

    Note: With Firebase Auth, the actual user creation (email/password) should 
    happen on the frontend using the Firebase Client SDK. The frontend then calls 
    this endpoint (or a Cloud Function) to create the user profile document in Firestore.

    Args:
        db: Firestore client
        data: Registration data (name, email)

    Returns:
        UserResponse: user info
    """
    # Block admin registration
    if data.role == "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin registration is not allowed. Please use the pre-defined admin account.",
        )

    # Determine approval status based on role
    is_approved = 1 if data.role == "user" else 0

    # Create the user profile in Firestore
    # We use a query to check if email exists to prevent duplicates, though Firebase Auth handles this too.
    users_ref = db.collection("users")
    existing = users_ref.where("email", "==", data.email).limit(1).get()
    
    if existing:
         raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered in Firestore.",
        )

    # Note: in a true Firebase flow, the document ID should be the Firebase Auth UID.
    # We'll let Firestore generate an ID for now if no UID is provided.
    new_user_ref = users_ref.document()
    user = User(
        id=new_user_ref.id,
        name=data.name,
        email=data.email,
        role=data.role,
        is_approved=is_approved,
    )
    
    new_user_ref.set(user.to_dict())

    logger.info(f"New user profile created: {user.email} (id={user.id}, role={user.role})")
    return UserResponse.model_validate(user.model_dump())


def login_user(db: firestore.Client, data: dict) -> dict:
    """
    With Firebase Auth, login is handled by the client SDK. 
    This endpoint is deprecated or can be used to just fetch the user profile 
    after the client logs in.
    """
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Login should be performed on the client-side using Firebase Auth SDK.",
    )


def get_current_user_from_token(db: Any, token: str) -> User:
    """
    Resolve a Firebase ID token to a User object.

    Args:
        db: Firestore client
        token: Firebase ID token string

    Returns:
        User: Authenticated user

    Raises:
        HTTPException 401: If token is invalid or user not found
    """
    payload = verify_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired Firebase token.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    email = payload.get("email")
    if not email:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload (no email).",
        )

    users_ref = db.collection("users")
    docs = users_ref.where("email", "==", email).limit(1).get()
    
    if not docs:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User profile not found in Firestore.",
        )
        
    user_doc = docs[0].to_dict()
    user_doc['id'] = docs[0].id
    
    return User(**user_doc)
