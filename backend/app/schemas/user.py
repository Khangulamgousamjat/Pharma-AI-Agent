"""
schemas/user.py — Pydantic schemas for User API request/response validation.

Separates API contract (schemas) from DB representation (models).
"""

from pydantic import BaseModel, EmailStr, Field
from datetime import datetime
from typing import Optional


class UserRegister(BaseModel):
    """Schema for POST /auth/register request body."""
    name: str = Field(..., min_length=2, max_length=100, description="User's display name")
    email: EmailStr = Field(..., description="Valid email address")
    password: str = Field(..., min_length=6, description="Password (min 6 characters)")


class UserLogin(BaseModel):
    """Schema for POST /auth/login request body."""
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    """
    Schema for user data returned in API responses.

    Excludes sensitive fields like password_hash.
    """
    id: int
    name: str
    email: str
    role: str
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True  # Allows creating from SQLAlchemy model instances


class TokenResponse(BaseModel):
    """Response schema for successful login."""
    access_token: str
    token_type: str = "bearer"
    user: UserResponse
