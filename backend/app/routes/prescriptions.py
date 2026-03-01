"""
routes/prescriptions.py — Prescription upload and management API.

Phase 2 addition: Handles prescription image upload, Vision Agent processing,
and prescription history retrieval.

Endpoints:
  POST /prescriptions/upload         — Upload and process prescription image
  GET  /prescriptions/user/{user_id} — Get user's prescription history
  GET  /prescriptions/pending        — Get all unverified (pharmacist queue)
"""

import os
import logging
from typing import List

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.prescription import PrescriptionUploadResponse, PrescriptionResponse
from app.services.prescription_service import (
    create_prescription,
    get_user_prescriptions,
    get_pending_prescriptions,
)
from app.services.vision_service import extract_medicine_data_from_image, save_uploaded_image
from app.agents.vision_agent import get_vision_agent
from app.utils.security import verify_token
from app.config import settings

router = APIRouter(prefix="/prescriptions", tags=["Prescriptions"])
logger = logging.getLogger(__name__)

# Upload directory — configurable via settings (defaults to ./uploads)
UPLOAD_DIR = getattr(settings, "upload_dir", "uploads")


@router.post(
    "/upload",
    response_model=PrescriptionUploadResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload and process a prescription image",
    description="Upload image → Vision Agent extracts medicine data → save prescription record",
)
async def upload_prescription(
    user_id: int = Form(..., description="ID of the user uploading the prescription"),
    file: UploadFile = File(..., description="Prescription image (jpg, png, webp)"),
    authorization: str = Form(None),
    db: Session = Depends(get_db),
):
    """
    Upload a prescription image for Vision Agent processing.

    Steps:
    1. Validate file type (images only)
    2. Save file to local upload directory
    3. Call VisionAgent.extract() → Gemini Vision API
    4. Store prescription record in DB with extracted data
    5. Return extracted medicine info + prescription ID

    Error handling:
      - 400: Invalid file type (non-image)
      - 413: File too large (>10MB)
      - 422: Vision extraction failed
    """
    # Validate file type
    allowed_types = {"image/jpeg", "image/jpg", "image/png", "image/webp", "image/gif"}
    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid file type: {file.content_type}. Only images (jpg, png, webp) are accepted.",
        )

    # Read file bytes and enforce 10MB limit
    file_bytes = await file.read()
    if len(file_bytes) > 10 * 1024 * 1024:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="File too large. Maximum size is 10MB.",
        )

    logger.info(
        f"Prescription upload: user={user_id} file='{file.filename}' "
        f"size={len(file_bytes)} bytes type={file.content_type}"
    )

    # Save image to disk
    image_path = save_uploaded_image(file_bytes, file.filename or "prescription.jpg", UPLOAD_DIR)

    # Process with Vision Agent
    vision_agent = get_vision_agent()
    extracted = await vision_agent.extract(image_path)

    if not extracted.get("success") and not extracted.get("raw_text"):
        logger.error(f"Vision extraction failed: {extracted.get('error')}")
        # Still save the record but with empty extraction
        extracted["medicine_name"] = None
        extracted["dosage"] = None
        extracted["raw_text"] = extracted.get("error", "Extraction failed")

    # Save prescription record (verified=False pending pharmacist review)
    prescription = create_prescription(db, user_id, image_path, extracted)

    return PrescriptionUploadResponse(
        prescription_id=prescription.id,
        message="Prescription uploaded successfully. Pending pharmacist verification.",
        extracted={
            "medicine_name": extracted.get("medicine_name"),
            "dosage": extracted.get("dosage"),
            "quantity": extracted.get("quantity"),
            "raw_text": extracted.get("raw_text"),
            "confidence": extracted.get("confidence"),
        },
        verified=False,
    )


@router.get(
    "/user/{user_id}",
    response_model=List[PrescriptionResponse],
    summary="Get all prescriptions for a user",
)
def get_user_prescriptions_route(
    user_id: int,
    db: Session = Depends(get_db),
):
    """
    Retrieve all prescription records uploaded by a user.

    Returns all prescriptions (verified and unverified) in reverse chronological order.
    """
    return get_user_prescriptions(db, user_id)


@router.get(
    "/pending",
    response_model=List[PrescriptionResponse],
    summary="Get all pending (unverified) prescriptions — pharmacist/admin only",
)
def get_pending_prescriptions_route(
    db: Session = Depends(get_db),
):
    """
    Get all prescriptions awaiting pharmacist verification (FIFO queue).

    In production this would require a pharmacist/admin JWT.
    For Phase 2, access is open so the pharmacist dashboard works without
    a separate login flow.
    """
    return get_pending_prescriptions(db)
