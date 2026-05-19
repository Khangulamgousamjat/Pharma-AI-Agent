"""
routes/voice_routes.py — Voice message API endpoint using Firestore.
"""

import logging
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from typing import Any, Optional

from app.firebase_db import get_db
from app.agents.voice_agent import get_voice_agent
from app.constants.languages import SUPPORTED_LANGUAGES, DEFAULT_LANGUAGE

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/agent", tags=["Voice Agent"])


class VoiceMessageRequest(BaseModel):
    user_id: str = Field(..., description="Authenticated user ID")
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
                "user_id": "user123",
                "message": "Mujhe paracetamol chahiye",
                "language": "hi",
            }
        }


class VoiceMessageResponse(BaseModel):
    response_text: str
    action: Optional[str] = None
    order_id: Optional[str] = None
    tts_url: Optional[str] = None
    language: str
    input_mode: str = "voice"


@router.post(
    "/voice-message",
    response_model=VoiceMessageResponse,
    summary="Process a voice transcript through the pharmacy agent",
)
async def voice_message(
    request: VoiceMessageRequest,
    db: Any = Depends(get_db),
):
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
)
async def get_supported_languages():
    return {
        "languages": [
            {"code": code, "name": name}
            for code, name in SUPPORTED_LANGUAGES.items()
        ],
        "default": DEFAULT_LANGUAGE,
    }
