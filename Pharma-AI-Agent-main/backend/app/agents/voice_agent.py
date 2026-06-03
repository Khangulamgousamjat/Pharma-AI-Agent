"""
agents/voice_agent.py — Voice conversation coordinator.

Phase 3 addition: Thin wrapper around the pharmacy agent that adds:
  - Language context tagging for multilingual responses
  - input_mode: "voice" metadata in LangSmith traces
  - Transcript + response logging for audit trail

Design choice: Rather than a separate LangChain agent, this is a
coordinator because the core ReAct logic lives in pharmacy_agent.py.
A separate agent would duplicate tools and increase latency unnecessarily.

LangSmith trace structure:
  parent: voice_agent_run
    └─ pharmacy_agent_run (existing tracing)
"""

import logging
from typing import Optional

from sqlalchemy.orm import Session

from app.constants.languages import (
    get_language_instruction,
    is_supported_language,
    DEFAULT_LANGUAGE,
)
from app.services.voice_service import process_voice_message

logger = logging.getLogger(__name__)


class VoiceAgent:
    """
    Voice conversation agent coordinator.

    Processes voice transcripts through the pharmacy agent with
    language context. Handles multilingual response generation.

    Usage:
        agent = VoiceAgent()
        result = await agent.process(
            transcript="Mujhe paracetamol chahiye",
            user_id=1,
            language="hi",
            db=db
        )
    """

    def __init__(self) -> None:
        self.logger = logging.getLogger(f"{__name__}.VoiceAgent")

    async def process(
        self,
        transcript: str,
        user_id: int,
        language: str,
        db: Session,
    ) -> dict:
        """
        Process a voice transcript and return agent response.

        Args:
            transcript: STT transcript text (from browser or server)
            user_id: Authenticated user ID
            language: ISO language code (en/hi/mr)
            db: Database session

        Returns:
            dict: {
                "response_text": str,   — Agent reply in requested language
                "action": str,          — order_created|prescription_required|info|error
                "order_id": int|None,
                "tts_url": str|None,    — Audio URL if server TTS enabled
                "language": str,        — Confirmed language code
                "input_mode": "voice",
            }
        """
        # Validate language code
        if not is_supported_language(language):
            self.logger.warning(
                f"[VoiceAgent] Unsupported language '{language}', "
                f"falling back to '{DEFAULT_LANGUAGE}'"
            )
            language = DEFAULT_LANGUAGE

        self.logger.info(
            f"[VoiceAgent] Processing voice message | user={user_id} | "
            f"language={language} | transcript='{transcript[:60]}...'"
        )

        # Delegate to voice service (which wraps pharmacy agent)
        result = await process_voice_message(
            transcript=transcript,
            user_id=user_id,
            language=language,
            db=db,
        )

        self.logger.info(
            f"[VoiceAgent] Completed | action={result.get('action')} | "
            f"order_id={result.get('order_id')}"
        )

        return result


# ---------------------------------------------------------------------------
# Module-level singleton for easy import
# ---------------------------------------------------------------------------

_voice_agent_instance: Optional[VoiceAgent] = None


def get_voice_agent() -> VoiceAgent:
    """
    Get (or create) the VoiceAgent singleton.

    Returns:
        VoiceAgent: Shared instance
    """
    global _voice_agent_instance
    if _voice_agent_instance is None:
        _voice_agent_instance = VoiceAgent()
    return _voice_agent_instance
