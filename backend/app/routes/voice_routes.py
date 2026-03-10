"""
routes/voice_routes.py — Voice message API endpoint.

Phase 3 addition: Receives STT transcripts from the frontend voice recorder
and processes them through the pharmacy agent with language context.

Endpoint: POST /agent/voice-message
Auth: JWT required
"""

import logging
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from app.database import SessionLocal, get_db
from app.agents.voice_agent import get_voice_agent
from app.constants.languages import SUPPORTED_LANGUAGES, DEFAULT_LANGUAGE

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/agent", tags=["Voice Agent"])

# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------

class VoiceMessageRequest(BaseModel):
    """Request body for voice message endpoint."""

    user_id: int = Field(..., description="Authenticated user ID")
    message: str = Field(
        ...,
        min_length=1,
        max_length=2000,
        description="STT transcript text (or typed message in voice mode)",
    )
    language: str = Field(
        default=DEFAULT_LANGUAGE,
        description="ISO language code: en | hi | mr",
    )

    class Config:
        json_schema_extra = {
            "example": {
                "user_id": 1,
                "message": "Mujhe paracetamol chahiye",
                "language": "hi",
            }
        }


class VoiceMessageResponse(BaseModel):
    """Response from voice message processing."""

    response_text: str
    action: str | None = None
    order_id: int | None = None
    tts_url: str | None = None
    language: str
    input_mode: str = "voice"


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@router.post(
    "/voice-message",
    response_model=VoiceMessageResponse,
    summary="Process a voice transcript through the pharmacy agent",
    description=(
        "Accepts a speech-to-text transcript and routes it through the "
        "pharmacy agent with language context. Use language='hi' for Hindi, "
        "'mr' for Marathi. TTS URL returned only if USE_SERVER_TTS=true."
    ),
)
async def voice_message(
    request: VoiceMessageRequest,
    db: Session = Depends(get_db),
):
    """
    Process voice transcript through pharmacy agent.

    Security: Caller must be authenticated (JWT validated).
    Rate limiting: Applied at middleware level (RATE_LIMIT_PER_MINUTE).

    Args:
        request: Voice message payload with transcript, user_id, language
        db: Database session

    Returns:
        VoiceMessageResponse: Agent reply text + action metadata
    """
    # Validate language
    if request.language not in SUPPORTED_LANGUAGES:
        logger.warning(
            f"[VoiceRoute] Unsupported language '{request.language}' "
            f"— falling back to '{DEFAULT_LANGUAGE}'"
        )
        language = DEFAULT_LANGUAGE
    else:
        language = request.language

    logger.info(
        f"[VoiceRoute] user={request.user_id} language={language} "
        f"transcript='{request.message[:60]}'"
    )

    voice_agent = get_voice_agent()
    result = await voice_agent.process(
        transcript=request.message,
        user_id=request.user_id,
        language=language,
        db=db,
    )

    return VoiceMessageResponse(
        response_text=result["response_text"],
        action=result.get("action"),
        order_id=result.get("order_id"),
        tts_url=result.get("tts_url"),
        language=result.get("language", language),
        input_mode="voice",
    )


@router.get(
    "/languages",
    summary="Get supported languages",
    description="Returns list of ISO codes and display names for supported languages.",
)
async def get_supported_languages():
    """Return all languages supported by the multilingual agent."""
    return {
        "languages": [
            {"code": code, "name": name}
            for code, name in SUPPORTED_LANGUAGES.items()
        ],
        "default": DEFAULT_LANGUAGE,
    }
