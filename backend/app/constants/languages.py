"""
config/languages.py — Central language configuration for PharmaAgent AI.

Phase 3 addition: Single source of truth for all supported languages.
To add a new language (e.g. French), add its ISO code to SUPPORTED_LANGUAGES.

The language code is passed to:
  - Gemini LLM prompts (instruct to reply in that language)
  - LangSmith traces (tagged for filtering)
  - Frontend: LanguageSelector.tsx
"""

from typing import Dict

# ---------------------------------------------------------------------------
# Supported Languages — ISO 639-1 code → display name
# ---------------------------------------------------------------------------
SUPPORTED_LANGUAGES: Dict[str, str] = {
    "en": "English",
    "hi": "हिंदी (Hindi)",
    "mr": "मराठी (Marathi)",
    # Add more below — no backend changes required beyond this dict:
    # "ta": "தமிழ் (Tamil)",
    # "te": "తెలుగు (Telugu)",
    # "fr": "Français (French)",
    # "ru": "Русский (Russian)",
}

# Default language when none specified by user or client
DEFAULT_LANGUAGE = "en"

# Languages where RTL text direction is required (future use)
RTL_LANGUAGES: list[str] = []


def get_language_name(code: str) -> str:
    """
    Get human-readable name for a language code.

    Args:
        code: ISO 639-1 language code (e.g. 'hi')

    Returns:
        str: Display name (e.g. 'हिंदी (Hindi)'), or 'Unknown' if not found
    """
    return SUPPORTED_LANGUAGES.get(code, "Unknown")


def is_supported_language(code: str) -> bool:
    """
    Check whether a language code is supported.

    Args:
        code: ISO 639-1 language code

    Returns:
        bool: True if code is in SUPPORTED_LANGUAGES
    """
    return code in SUPPORTED_LANGUAGES


def get_language_instruction(code: str) -> str:
    """
    Build a Gemini-compatible language instruction string.

    This is embedded in agent prompts to instruct Gemini to reply
    in the user's preferred language without needing a separate
    translation step (reduces cost and latency).

    Args:
        code: ISO 639-1 language code

    Returns:
        str: Instruction text for embedding in system prompt
    """
    if code == "en" or code not in SUPPORTED_LANGUAGES:
        return "Reply in English."
    name = SUPPORTED_LANGUAGES[code]
    return (
        f"Reply in {name}. Use simple, clear language appropriate for a patient. "
        f"If you quote medicine names or dosages, keep those in their original form."
    )
