"""
services/voice_service.py — Voice message processing and optional server TTS.

Phase 3 addition: Handles the backend side of voice chat.

Architecture:
  - PRIMARY: Browser-based STT/TTS (Web Speech API) — zero backend cost.
  - FALLBACK: Client sends transcript text → backend runs pharmacy agent →
    returns text response (client's TTS plays it).
  - OPTIONAL: If TTS_PROVIDER=gemini or other, backend can generate audio blob.

This service is intentionally thin — it wraps the existing pharmacy agent
with language context. The heavy lifting stays in pharmacy_agent.py.

Privacy note (per requirements):
  - Browser-mode: audio never leaves the client device.
  - Server fallback: transcript text transmitted (not audio) by default.
  - Audio file upload (if ALLOW_SERVER_AUDIO_UPLOAD=true): WAV sent to backend
    but only transcript is stored, raw audio is not persisted.
"""

import logging
from typing import Optional

from sqlalchemy.orm import Session

from app.config import settings
from app.constants.languages import get_language_instruction, DEFAULT_LANGUAGE, is_supported_language

logger = logging.getLogger(__name__)


async def process_voice_message(
    transcript: str,
    user_id: int,
    language: str,
    db: Session,
) -> dict:
    """
    Process a voice transcript through the pharmacy agent.

    Takes the STT transcript (from browser or server fallback),
    runs it through the pharmacy agent with language context,
    and returns a structured response for the client to display
    and optionally speak via TTS.

    Args:
        transcript: User's speech as text
        user_id: Authenticated user ID
        language: ISO language code (en/hi/mr)
        db: Database session

    Returns:
        dict: {
            "response_text": str,       — Agent's text reply
            "action": str,              — order_created / prescription_required / info
            "order_id": int | None,
            "tts_url": str | None,      — Only set if server-side TTS enabled
            "language": str,            — Echo back for client confirmation
        }
    """
    # Validate language — fall back to default if unsupported
    if not is_supported_language(language):
        logger.warning(f"[Voice] Unsupported language '{language}' — using '{DEFAULT_LANGUAGE}'")
        language = DEFAULT_LANGUAGE

    # Build language-aware message (inject language instruction into transcript)
    lang_instruction = get_language_instruction(language)
    enhanced_message = f"{transcript}\n\n[Language instruction: {lang_instruction}]"

    logger.info(
        f"[Voice] Processing transcript from user={user_id} "
        f"language={language}: '{transcript[:80]}'"
    )

    # Delegate to pharmacy agent (reuse existing agent - avoids code duplication)
    from app.agents.pharmacy_agent import get_pharmacy_agent
    from app.agents.tools import set_db_session

    set_db_session(db)
    agent = get_pharmacy_agent()

    try:
        result = await agent.chat(
            user_id=user_id,
            message=enhanced_message,
            db=db,
        )

        # Optional server-side TTS
        tts_url = None
        if settings.use_server_tts and settings.tts_provider != "none":
            tts_url = await _generate_tts(result["response"], language)

        return {
            "response_text": result["response"],
            "action": result.get("action", "info"),
            "order_id": result.get("order_id"),
            "tts_url": tts_url,
            "language": language,
            "input_mode": "voice",
        }

    except Exception as e:
        logger.error(f"[Voice] Processing failed: {e}", exc_info=True)
        return {
            "response_text": "I encountered an error processing your voice message. Please try again.",
            "action": "error",
            "order_id": None,
            "tts_url": None,
            "language": language,
            "input_mode": "voice",
        }


async def _generate_tts(text: str, language: str) -> Optional[str]:
    """
    Optional server-side TTS generation.

    Currently a stub — returns None unless TTS_PROVIDER is configured.

    To add ElevenLabs or other TTS:
      1. Set TTS_PROVIDER=elevenlabs in .env
      2. Add ELEVENLABS_API_KEY to .env
      3. Implement the API call below

    Args:
        text: Text to convert to speech
        language: ISO language code

    Returns:
        str | None: URL or path to audio file, or None if TTS not configured
    """
    if settings.tts_provider == "none":
        return None

    # TODO: Implement TTS provider integration
    # Example structure for future implementation:
    # if settings.tts_provider == "elevenlabs":
    #     audio_bytes = await call_elevenlabs_api(text, language)
    #     path = save_audio_file(audio_bytes)
    #     return f"/audio/{path}"

    logger.warning(f"[Voice] TTS provider '{settings.tts_provider}' not implemented — returning None")
    return None
