"""
models/user.py — Firestore schema for the Users collection.
"""

from pydantic import BaseModel, EmailStr, Field
from datetime import datetime
from typing import Optional

class User(BaseModel):
    """
    User Firestore document schema.
    """
    id: str = Field(description="Firestore Document ID (Firebase Auth UID)")
    name: str
    email: EmailStr
    role: str = "user"
    is_approved: int = 1
    ui_theme: str = "dark"
    preferred_language: str = "en"
    created_at: datetime = Field(default_factory=datetime.utcnow)

    def to_dict(self):
        return self.model_dump(exclude={'id'})
