"""
services/vision_service.py — Gemini Vision API integration for prescription scanning.

Phase 2 addition: Uses Google Gemini's multimodal capabilities to extract
structured medicine information from images of:
  - Handwritten prescriptions
  - Printed medicine labels / packaging
  - Medical bills / receipts

The extraction returns structured JSON that the pharmacy agent uses to
validate and potentially automate order creation.

Integration notes:
  - Uses google-generativeai (Gemini 2.0 Flash vision model)
  - Falls back gracefully if vision extraction fails (returns raw text)
  - Images are saved locally before being sent to the API
"""

import base64
import json
import logging
import os
from pathlib import Path
from typing import Optional

import google.generativeai as genai
from app.config import settings

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Vision Model Configuration
# ---------------------------------------------------------------------------
# We re-use the same Gemini API key from backend settings.
# The vision model uses multimodal input (text prompt + image bytes).
# ---------------------------------------------------------------------------
_vision_model = None


def _get_vision_model():
    """
    Initialize and return the Gemini Vision model (singleton).

    Returns:
        genai.GenerativeModel: Configured Gemini model for vision tasks
    """
    global _vision_model
    if _vision_model is None:
        genai.configure(api_key=settings.gemini_api_key)
        _vision_model = genai.GenerativeModel("gemini-2.5-flash")
        logger.info("Vision model initialized: gemini-2.5-flash")
    return _vision_model


# ---------------------------------------------------------------------------
# Extraction Prompt
# ---------------------------------------------------------------------------
EXTRACTION_PROMPT = """
You are a medical prescription scanner AI. Analyze this image carefully.

Extract the following information if present:
1. Medicine name (exact name as written)
2. Dosage (e.g., 500mg, 10mg)
3. Quantity (number of tablets/bottles)
4. Any additional instructions

Respond ONLY with a valid JSON object in this exact format:
{
  "medicine_name": "extracted medicine name or null",
  "dosage": "extracted dosage or null",
  "quantity": extracted_number_or_null,
  "instructions": "any dosage instructions or null",
  "raw_text": "all text you can read from the image",
  "confidence": "high/medium/low"
}

If the image is not a prescription or you cannot read it clearly, still return
the JSON with null values and explain in raw_text what you see.
"""


async def extract_medicine_data_from_image(image_path: str) -> dict:
    """
    Extract structured medicine data from a prescription image using Gemini Vision.

    Process:
    1. Reads the image file from disk
    2. Encodes it as base64
    3. Sends to Gemini Vision with a structured extraction prompt
    4. Parses the JSON response into a typed dict

    Args:
        image_path: Absolute path to the saved image file

    Returns:
        dict: Structured extraction result:
            {
                "medicine_name": str | None,
                "dosage": str | None,
                "quantity": int | None,
                "instructions": str | None,
                "raw_text": str | None,
                "confidence": "high" | "medium" | "low",
                "success": bool,
                "error": str | None  (only if success=False)
            }
    """
    logger.info(f"[VisionService] Processing image: {image_path}")

    # Verify file exists
    if not os.path.exists(image_path):
        logger.error(f"[VisionService] Image file not found: {image_path}")
        return {
            "success": False,
            "error": f"Image file not found: {image_path}",
            "medicine_name": None,
            "dosage": None,
            "quantity": None,
            "instructions": None,
            "raw_text": None,
            "confidence": "low",
        }

    try:
        # Read and encode the image
        with open(image_path, "rb") as img_file:
            image_data = img_file.read()

        # Determine MIME type from extension
        ext = Path(image_path).suffix.lower()
        mime_map = {
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".png": "image/png",
            ".gif": "image/gif",
            ".webp": "image/webp",
        }
        mime_type = mime_map.get(ext, "image/jpeg")

        # Build multimodal request for Gemini
        model = _get_vision_model()
        image_part = {
            "mime_type": mime_type,
            "data": image_data,
        }

        # Send to Gemini Vision API
        logger.info(f"[VisionService] Sending {len(image_data)} bytes to Gemini Vision...")
        response = model.generate_content([EXTRACTION_PROMPT, image_part])

        raw_response = response.text.strip()
        logger.info(f"[VisionService] Raw response: {raw_response[:200]}...")

        # Parse JSON from response (strip markdown code blocks if present)
        clean_json = raw_response
        if "```json" in clean_json:
            clean_json = clean_json.split("```json")[1].split("```")[0].strip()
        elif "```" in clean_json:
            clean_json = clean_json.split("```")[1].split("```")[0].strip()

        extracted = json.loads(clean_json)

        # Normalize quantity to int if it came as string
        if extracted.get("quantity") and isinstance(extracted["quantity"], str):
            try:
                extracted["quantity"] = int(extracted["quantity"])
            except ValueError:
                extracted["quantity"] = None

        extracted["success"] = True
        extracted["error"] = None

        logger.info(
            f"[VisionService] Extracted: medicine='{extracted.get('medicine_name')}' "
            f"dosage='{extracted.get('dosage')}' qty={extracted.get('quantity')} "
            f"confidence={extracted.get('confidence')}"
        )
        return extracted

    except json.JSONDecodeError as e:
        # Vision model returned text but not valid JSON — extract key info from raw text
        logger.warning(f"[VisionService] JSON parse failed: {e}. Using raw response as fallback.")
        return {
            "success": True,  # Partial success — we have raw text
            "error": None,
            "medicine_name": None,
            "dosage": None,
            "quantity": None,
            "instructions": None,
            "raw_text": raw_response[:2000] if 'raw_response' in locals() else "Could not read image",
            "confidence": "low",
        }

    except Exception as e:
        logger.error(f"[VisionService] Vision extraction failed: {e}", exc_info=True)
        return {
            "success": False,
            "error": str(e),
            "medicine_name": None,
            "dosage": None,
            "quantity": None,
            "instructions": None,
            "raw_text": None,
            "confidence": "low",
        }


def save_uploaded_image(file_bytes: bytes, filename: str, upload_dir: str) -> str:
    """
    Save an uploaded prescription image to the local filesystem.

    Creates the upload directory if it does not exist.
    Appends a timestamp to avoid filename collisions.

    Args:
        file_bytes: Raw image bytes from the multipart upload
        filename: Original filename from the upload request
        upload_dir: Base directory for storing uploads

    Returns:
        str: Absolute path to the saved file
    """
    import time

    # Create upload directory if it doesn't exist
    os.makedirs(upload_dir, exist_ok=True)

    # Generate unique filename to avoid collisions
    timestamp = int(time.time())
    ext = Path(filename).suffix.lower() or ".jpg"
    safe_name = f"prescription_{timestamp}{ext}"
    save_path = os.path.join(upload_dir, safe_name)

    with open(save_path, "wb") as f:
        f.write(file_bytes)

    logger.info(f"[VisionService] Image saved: {save_path} ({len(file_bytes)} bytes)")
    return save_path
