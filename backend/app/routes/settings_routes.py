"""
routes/settings_routes.py — User settings (theme + language) endpoints.

Phase 3 addition: Allows users to persist their UI preferences in the DB.
On login, these preferences are returned and synced to localStorage.

Endpoints:
  GET  /settings/preferences          — Get current user preferences
  PUT  /settings/preferences          — Update user preferences

These preferences are:
  - ui_theme: 'dark' | 'light'
  - preferred_language: ISO code (en/hi/mr)
"""

import logging
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from typing import Literal, Annotated

from app.database import SessionLocal, get_db
from app.models.user import User
from app.utils.security import verify_token
from app.constants.languages import SUPPORTED_LANGUAGES

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/settings", tags=["User Settings"])



# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------

class UserPreferences(BaseModel):
    """User UI personalisation preferences."""
    ui_theme: Literal["dark", "light"] = Field(default="dark", description="UI color theme")
    preferred_language: str = Field(
        default="en",
        description="ISO language code: en|hi|mr",
    )


class PreferencesResponse(UserPreferences):
    user_id: int
    name: str
    email: str
    role: str


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@router.get(
    "/preferences",
    response_model=PreferencesResponse,
    summary="Get user preferences",
    description="Returns the current user's UI theme and language preference.",
)
def get_preferences(
    user_id: int,
    db: Annotated[Session, Depends(get_db)],
):
    """
    Retrieve persisted preferences for a user.

    Args:
        user_id: User ID (from client session)
        db: Database session

    Returns:
        PreferencesResponse: Theme + language + user info
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return PreferencesResponse(
        user_id=user.id,
        name=user.name,
        email=user.email,
        role=user.role,
        ui_theme=user.ui_theme or "dark",
        preferred_language=user.preferred_language or "en",
    )


@router.put(
    "/preferences",
    response_model=PreferencesResponse,
    summary="Update user preferences",
    description="Save UI theme and language preference to the database.",
)
def update_preferences(
    user_id: int,
    preferences: UserPreferences,
    db: Annotated[Session, Depends(get_db)],
):
    """
    Persist user UI preferences to database.

    Also validates language code against supported languages list.

    Args:
        user_id: User ID (from client session)
        preferences: New theme and language values
        db: Database session

    Returns:
        PreferencesResponse: Updated preferences
    """
    # Validate language
    if preferences.preferred_language not in SUPPORTED_LANGUAGES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported language '{preferences.preferred_language}'. "
                   f"Supported: {list(SUPPORTED_LANGUAGES.keys())}",
        )

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user.ui_theme = preferences.ui_theme
    user.preferred_language = preferences.preferred_language
    db.commit()
    db.refresh(user)

    logger.info(f"[Settings] Updated user={user_id} theme={preferences.ui_theme} lang={preferences.preferred_language}")

    return PreferencesResponse(
        user_id=user.id,
        name=user.name,
        email=user.email,
        role=user.role,
        ui_theme=user.ui_theme,
        preferred_language=user.preferred_language,
    )
