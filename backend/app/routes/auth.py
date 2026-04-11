"""
routes/auth.py — Authentication endpoints: register and login.

Routes:
    POST /auth/register  — Create a new account
    POST /auth/login     — Get a JWT token

These routes delegate all business logic to auth_service.py.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import Annotated

from app.database import get_db
from app.schemas.user import UserRegister, UserLogin, TokenResponse
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
