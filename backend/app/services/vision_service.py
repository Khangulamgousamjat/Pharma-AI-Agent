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
  - Images are uploaded to Firebase Storage
"""

import base64
import json
import logging
import os
import time
from pathlib import Path
from typing import Optional

import firebase_admin
from firebase_admin import credentials, storage
import google.generativeai as genai
from app.config import settings

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Firebase Storage Initialization
# ---------------------------------------------------------------------------
_firebase_initialized = False

def _init_firebase():
    """Initialize Firebase Admin SDK (singleton — only once at startup)."""
    global _firebase_initialized
    if _firebase_initialized:
        return
    try:
        cred_path = settings.firebase_credentials_json
        bucket_name = settings.firebase_storage_bucket

        if not os.path.exists(cred_path):
            logger.warning(
                f"[Firebase] Credentials file not found at '{cred_path}'. "
                "Image uploads will be disabled. "
                "Set FIREBASE_CREDENTIALS_JSON and FIREBASE_STORAGE_BUCKET in .env"
            )
            return

        if not bucket_name:
            logger.warning(
                "[Firebase] FIREBASE_STORAGE_BUCKET is not set. "
                "Image uploads will be disabled."
            )
            return

        cred = credentials.Certificate(cred_path)
        if not firebase_admin._apps:
            firebase_admin.initialize_app(cred, {"storageBucket": bucket_name})
            logger.info(f"[Firebase] Storage initialized. Bucket: {bucket_name}")
        _firebase_initialized = True
    except Exception as e:
        logger.error(f"[Firebase] Initialization failed: {e}", exc_info=True)


# Initialize on module import
_init_firebase()


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


async def extract_medicine_data_from_image(file_bytes: bytes, filename: str) -> dict:
    """
    Extract structured medicine data from a prescription image using Gemini Vision.

    Process:
    1. Reads memory bytes directly
    2. Determines MIME type
    3. Sends to Gemini Vision with a structured extraction prompt
    4. Parses the JSON response into a typed dict

    Args:
        file_bytes: Raw bytes of the image
        filename: Name of the file uploaded

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
    logger.info(f"[VisionService] Processing image bytes: {filename}")

    try:
        # Determine MIME type from extension
        ext = Path(filename).suffix.lower()
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
            "data": file_bytes,
        }

        # Send to Gemini Vision API
        logger.info(f"[VisionService] Sending {len(file_bytes)} bytes to Gemini Vision...")
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


def save_uploaded_image(file_bytes: bytes, filename: str) -> str:
    """
    Upload a prescription image to Firebase Storage.

    Args:
        file_bytes: Raw image bytes from the multipart upload
        filename: Original filename from the upload request

    Returns:
        str: Public URL of the uploaded file in Firebase Storage
    """
    if not _firebase_initialized:
        raise ValueError(
            "Firebase Storage is not configured. "
            "Please set FIREBASE_CREDENTIALS_JSON and FIREBASE_STORAGE_BUCKET in .env "
            "and place your firebase-credentials.json in the backend directory."
        )

    # Generate unique filename to avoid collisions
    timestamp = int(time.time())
    ext = Path(filename).suffix.lower() or ".jpg"
    safe_name = f"prescriptions/prescription_{timestamp}{ext}"

    try:
        # Determine content type
        content_type = "image/jpeg"
        if ext == ".png":
            content_type = "image/png"
        elif ext == ".webp":
            content_type = "image/webp"
        elif ext == ".gif":
            content_type = "image/gif"

        # Upload to Firebase Storage
        bucket = storage.bucket()
        blob = bucket.blob(safe_name)
        blob.upload_from_string(file_bytes, content_type=content_type)

        # Make publicly accessible and get URL
        blob.make_public()
        public_url = blob.public_url

        logger.info(f"[VisionService] Image uploaded to Firebase Storage: {public_url}")
        return public_url

    except Exception as e:
        logger.error(f"[VisionService] Firebase Storage upload failed: {e}")
        raise e
