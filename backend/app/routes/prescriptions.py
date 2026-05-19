"""
routes/prescriptions.py — Prescription upload and management API using Firestore.
"""

import os
import logging
from typing import List, Any

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status

from app.firebase_db import get_db
from app.schemas.prescription import PrescriptionUploadResponse, PrescriptionResponse
from app.services.prescription_service import (
    create_prescription,
    get_user_prescriptions,
    get_pending_prescriptions,
)
from app.services.vision_service import save_uploaded_image
from app.agents.vision_agent import get_vision_agent
from app.config import settings

router = APIRouter(prefix="/prescriptions", tags=["Prescriptions"])
logger = logging.getLogger(__name__)


@router.post(
    "/upload",
    response_model=PrescriptionUploadResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload and process a prescription image",
)
async def upload_prescription(
    user_id: str = Form(..., description="ID of the user uploading the prescription"),
    file: UploadFile = File(..., description="Prescription image (jpg, png, webp)"),
    db: Any = Depends(get_db),
    authorization: str = Form(None),
):
    allowed_types = {"image/jpeg", "image/jpg", "image/png", "image/webp", "image/gif"}
    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid file type: {file.content_type}. Only images (jpg, png, webp) are accepted.",
        )

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

    # Save image to Firebase Storage
    image_url = save_uploaded_image(file_bytes, file.filename or "prescription.jpg")

    # Process with Vision Agent using raw bytes
    vision_agent = get_vision_agent()
    extracted = await vision_agent.extract(file_bytes, file.filename or "prescription.jpg")

    if not extracted.get("success") and not extracted.get("raw_text"):
        logger.error(f"Vision extraction failed: {extracted.get('error')}")
        extracted["medicine_name"] = None
        extracted["dosage"] = None
        extracted["raw_text"] = extracted.get("error", "Extraction failed")

    prescription = create_prescription(db, user_id, image_url, extracted)

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
    user_id: str,
    db: Any = Depends(get_db),
):
    return get_user_prescriptions(db, user_id)


@router.get(
    "/pending",
    response_model=List[PrescriptionResponse],
    summary="Get all pending (unverified) prescriptions — pharmacist/admin only",
)
def get_pending_prescriptions_route(
    db: Any = Depends(get_db),
):
    return get_pending_prescriptions(db)
