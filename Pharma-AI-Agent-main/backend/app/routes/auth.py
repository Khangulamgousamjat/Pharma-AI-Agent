"""
routes/auth.py — Authentication endpoints: register and login.

Routes:
    POST /auth/register  — Create a new account
    POST /auth/login     — Get a JWT token

These routes delegate all business logic to auth_service.py.
"""

from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.orm import Session
from typing import Annotated, Optional

from app.database import get_db
from app.schemas.user import UserRegister, UserLogin, TokenResponse, UserResponse
from app.services.auth_service import register_user, login_user

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=TokenResponse, status_code=201)
async def register(data: UserRegister, db: Annotated[Session, Depends(get_db)]):
    """
    Register a new user account.

    Returns a JWT token and user info on success (auto-login after register).

    Args:
        data: Registration form (name, email, password)
        db: Database session (injected by FastAPI)
    """
    return register_user(db, data)


@router.post("/login", response_model=TokenResponse)
async def login(data: UserLogin, db: Annotated[Session, Depends(get_db)]):
    """
    Authenticate an existing user.

    Returns a JWT access token valid for 24 hours.

    Args:
        data: Login credentials (email, password)
        db: Database session (injected by FastAPI)
    """
    return login_user(db, data)


@router.get("/me", response_model=UserResponse)
async def get_me(
    db: Annotated[Session, Depends(get_db)],
    authorization: Optional[str] = Header(None)
):
    """
    Get current logged in user profile details.
    Resolves both JWT and Firebase tokens.
    """
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Authorization header required.")
    token = authorization.split(" ")[1]
    
    from app.services.auth_service import get_current_user_from_token
    user = get_current_user_from_token(db, token)
    return user
