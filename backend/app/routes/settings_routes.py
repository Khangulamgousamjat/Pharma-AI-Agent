"""
routes/settings_routes.py — User settings (theme + language) endpoints using Firestore.
"""

import logging
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from typing import Literal, Any

from app.firebase_db import get_db
from app.utils.security import verify_token
from app.constants.languages import SUPPORTED_LANGUAGES

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/settings", tags=["User Settings"])


class UserPreferences(BaseModel):
    ui_theme: Literal["dark", "light"] = Field(default="dark", description="UI color theme")
    preferred_language: str = Field(
        default="en",
        description="ISO language code: en|hi|mr",
    )


class PreferencesResponse(UserPreferences):
    user_id: str
    name: str
    email: str
    role: str


@router.get(
    "/preferences",
    response_model=PreferencesResponse,
    summary="Get user preferences",
)
def get_preferences(
    user_id: str,
    db: Any = Depends(get_db),
):
    doc = db.collection("users").document(user_id).get()
    if not doc.exists:
        raise HTTPException(status_code=404, detail="User not found")

    user = doc.to_dict()
    return PreferencesResponse(
        user_id=doc.id,
        name=user.get("name", ""),
        email=user.get("email", ""),
        role=user.get("role", "user"),
        ui_theme=user.get("ui_theme") or "dark",
        preferred_language=user.get("preferred_language") or "en",
    )


@router.put(
    "/preferences",
    response_model=PreferencesResponse,
    summary="Update user preferences",
)
def update_preferences(
    user_id: str,
    preferences: UserPreferences,
    db: Any = Depends(get_db),
):
    if preferences.preferred_language not in SUPPORTED_LANGUAGES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported language '{preferences.preferred_language}'. "
                   f"Supported: {list(SUPPORTED_LANGUAGES.keys())}",
        )

    doc_ref = db.collection("users").document(user_id)
    doc = doc_ref.get()
    if not doc.exists:
        raise HTTPException(status_code=404, detail="User not found")

    doc_ref.update({
        "ui_theme": preferences.ui_theme,
        "preferred_language": preferences.preferred_language
    })

    user = doc_ref.get().to_dict()

    logger.info(f"[Settings] Updated user={user_id} theme={preferences.ui_theme} lang={preferences.preferred_language}")

    return PreferencesResponse(
        user_id=doc_ref.id,
        name=user.get("name", ""),
        email=user.get("email", ""),
        role=user.get("role", "user"),
        ui_theme=user.get("ui_theme"),
        preferred_language=user.get("preferred_language"),
    )
