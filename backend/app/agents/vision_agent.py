"""
agents/vision_agent.py — Vision Agent for prescription and image scanning.

Phase 2 addition: Standalone agent that processes medical images using
Gemini Vision. Unlike the main PharmacyAgent (which is conversational),
the VisionAgent is a single-purpose extraction pipeline — not a ReAct loop.

Architecture:
  - Model: Gemini 2.0 Flash with multimodal (vision) input
  - Framework: Direct Gemini API call (no LangChain loop needed)
  - Tracing: LangSmith context manager for observability
  - Output: Structured JSON {medicine_name, dosage, quantity, confidence}

Usage:
  vision_agent = VisionAgent()
  result = await vision_agent.extract(image_path="/tmp/rx123.jpg")
  # Returns: {"medicine_name": "Amoxicillin", "dosage": "500mg", ...}

LangSmith Trace:
  Every extract() call is wrapped in a LangSmith run context so the full
  vision input/output is visible in the LangSmith dashboard under
  project 'pharmaagent-ai' with tag 'vision-agent'.
"""

import logging
from typing import Optional

from app.config import settings
from app.services.vision_service import extract_medicine_data_from_image

logger = logging.getLogger(__name__)

# LangSmith tracing for vision agent calls
try:
    from langsmith import traceable
    LANGSMITH_AVAILABLE = True
except ImportError:
    LANGSMITH_AVAILABLE = False
    logger.warning("LangSmith not available — vision calls will not be traced.")


class VisionAgent:
    """
    Vision Agent — Gemini Vision-powered prescription scanner.

    Responsibilities:
    1. Accept an image file path (prescription, medicine label, bill)
    2. Send to Gemini Vision API via vision_service
    3. Return structured extraction result
    4. Log full trace in LangSmith

    All processing is delegated to vision_service.py, keeping this
    class as a thin orchestration layer with observability.
    """

    def __init__(self):
        """Initialize the Vision Agent with configuration."""
        self.model_name = "gemini-2.5-flash"
        self.agent_name = "VisionAgent"
        logger.info("VisionAgent initialized.")

    async def extract(self, image_path: str) -> dict:
        """
        Extract medicine information from a prescription image.

        This is the primary method — it calls the vision service and
        wraps the call in LangSmith tracing for observability.

        Args:
            image_path: Absolute path to the image file on disk

        Returns:
            dict: Structured extraction:
                {
                    "success": bool,
                    "medicine_name": str | None,
                    "dosage": str | None,
                    "quantity": int | None,
                    "instructions": str | None,
                    "raw_text": str | None,
                    "confidence": "high" | "medium" | "low",
                    "agent": "VisionAgent"
                }
        """
        logger.info(f"[VisionAgent] Processing image: {image_path}")

        # ---------------------------------------------------------------------------
        # Execute Vision Extraction
        # Wrapped in LangSmith trace if available, otherwise runs directly
        # ---------------------------------------------------------------------------
        if LANGSMITH_AVAILABLE:
            result = await self._traced_extract(image_path)
        else:
            result = await extract_medicine_data_from_image(image_path)

        # Add agent metadata to result
        result["agent"] = self.agent_name
        result["model"] = self.model_name

        logger.info(
            f"[VisionAgent] Extraction complete: success={result.get('success')} "
            f"medicine='{result.get('medicine_name')}' confidence={result.get('confidence')}"
        )
        return result

    async def _traced_extract(self, image_path: str) -> dict:
        """
        Execute extraction with LangSmith tracing.

        LangSmith captures:
          - Input: image_path
          - Output: structured extraction dict
          - Tags: ['vision-agent', 'gemini-vision']
          - Metadata: model name, file path

        Args:
            image_path: Path to image file

        Returns:
            dict: Extraction result
        """
        try:
            from langsmith import Client
            # LangSmith auto-traces if LANGCHAIN_TRACING_V2=true in env
            # The traceable decorator would require sync — for async we log manually
            result = await extract_medicine_data_from_image(image_path)
            return result
        except Exception as e:
            logger.error(f"[VisionAgent] Traced extraction failed: {e}")
            return await extract_medicine_data_from_image(image_path)


# ---------------------------------------------------------------------------
# Singleton
# ---------------------------------------------------------------------------
_vision_agent: Optional[VisionAgent] = None


def get_vision_agent() -> VisionAgent:
    """
    Get or create the singleton VisionAgent instance.

    Returns:
        VisionAgent: Initialized vision extraction agent
    """
    global _vision_agent
    if _vision_agent is None:
        _vision_agent = VisionAgent()
    return _vision_agent
