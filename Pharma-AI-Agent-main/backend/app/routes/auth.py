"""
routes/auth.py — Authentication endpoints: register and profile lookup.

Routes:
    POST /auth/register  — Create a new account profile
    GET /auth/me         — Get current user profile from token

With Firebase Auth, the frontend handles the actual login and JWT generation.
These routes just manage the Firestore user profiles.
"""

from fastapi import APIRouter, Depends, Header, HTTPException, status
from typing import Annotated, Optional
from firebase_admin import firestore

from app.firebase_db import get_db
from app.schemas.user import UserRegister, UserResponse
from app.services.auth_service import register_user, get_current_user_from_token

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=UserResponse, status_code=201)
async def register(data: UserRegister, db: firestore.Client = Depends(get_db)):
    """
    Register a new user account profile in Firestore.

    Args:
        data: Registration form (name, email, role, password ignored)
    """
    return register_user(db, data)


@router.get("/me", response_model=UserResponse)
async def get_me(
    db: firestore.Client = Depends(get_db),
    authorization: Optional[str] = Header(None)
):
    """
    Fetch the currently authenticated user's profile using their Firebase JWT.
    """
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization header missing or invalid.",
        )
        
    token = authorization.split(" ")[1]
    user = get_current_user_from_token(db, token)
    return user
