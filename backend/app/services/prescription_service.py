"""
services/prescription_service.py — Business logic for prescription management.

Phase 2 addition: Handles the prescription lifecycle:
  upload → extract → pending review → pharmacist verify → allow Rx orders
"""

import json
import logging
from typing import List, Optional

from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.models.prescription import Prescription

logger = logging.getLogger(__name__)


def create_prescription(
    db: Session,
    user_id: int,
    image_url: str,
    extracted_data: dict,
) -> Prescription:
    """
    Create a new prescription record after Vision Agent extraction.

    Stores both the raw extracted text and structured medicine JSON.
    Sets verified=False — pharmacist must explicitly verify.

    Args:
        db: Database session
        user_id: Patient's user ID
        image_url: Local path to saved image
        extracted_data: Dict from vision_service.extract_medicine_data_from_image()

    Returns:
        Prescription: Newly created prescription record
    """
    # Serialize the full extracted dict as JSON for storage
    extracted_text = extracted_data.get("raw_text", "")
    extracted_medicine = json.dumps({
        "medicine_name": extracted_data.get("medicine_name"),
        "dosage": extracted_data.get("dosage"),
        "quantity": extracted_data.get("quantity"),
        "instructions": extracted_data.get("instructions"),
        "confidence": extracted_data.get("confidence"),
    })

    prescription = Prescription(
        user_id=user_id,
        image_url=image_url,
        extracted_text=extracted_text,
        extracted_medicine=extracted_medicine,
        verified=False,
    )
    db.add(prescription)
    db.commit()
    db.refresh(prescription)

    logger.info(
        f"Prescription created: id={prescription.id} user={user_id} "
        f"medicine='{extracted_data.get('medicine_name')}'"
    )
    return prescription


def get_user_prescriptions(db: Session, user_id: int) -> List[Prescription]:
    """
    Get all prescriptions uploaded by a user.

    Args:
        db: Database session
        user_id: Patient's user ID

    Returns:
        List[Prescription]: All prescriptions, newest first
    """
    return (
        db.query(Prescription)
        .filter(Prescription.user_id == user_id)
        .order_by(Prescription.created_at.desc())
        .all()
    )


def get_pending_prescriptions(db: Session) -> List[Prescription]:
    """
    Get all unverified prescriptions (pharmacist queue).

    Returns:
        List[Prescription]: Unverified prescriptions, oldest first (FIFO queue)
    """
    return (
        db.query(Prescription)
        .filter(Prescription.verified == False)  # noqa: E712
        .order_by(Prescription.created_at.asc())
        .all()
    )


def verify_prescription(
    db: Session,
    prescription_id: int,
    pharmacist_id: int,
) -> Prescription:
    """
    Mark a prescription as verified by a pharmacist.

    This is the gate that unlocks Rx medicine ordering for the user.
    Records which pharmacist verified it for full audit trail.

    Args:
        db: Database session
        prescription_id: Prescription to verify
        pharmacist_id: User ID of the approving pharmacist

    Returns:
        Prescription: Updated verified prescription

    Raises:
        HTTPException 404: If prescription not found
        HTTPException 400: If prescription already verified
    """
    prescription = db.query(Prescription).filter(Prescription.id == prescription_id).first()
    if not prescription:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Prescription id={prescription_id} not found.",
        )

    if prescription.verified:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Prescription is already verified.",
        )

    prescription.verified = True
    prescription.verified_by = pharmacist_id
    db.commit()
    db.refresh(prescription)

    logger.info(
        f"Prescription verified: id={prescription_id} by pharmacist={pharmacist_id}"
    )
    return prescription


def has_verified_prescription_for_medicine(
    db: Session,
    user_id: int,
    medicine_name: str,
) -> bool:
    """
    Check if a user has a verified prescription for a given medicine.

    Used by the Safety Agent before allowing Rx medicine orders.
    Performs a case-insensitive substring match on extracted_medicine JSON.

    Args:
        db: Database session
        user_id: Patient's user ID
        medicine_name: Name of the medicine (partial match supported)

    Returns:
        bool: True if a verified prescription exists for this medicine
    """
    prescriptions = (
        db.query(Prescription)
        .filter(
            Prescription.user_id == user_id,
            Prescription.verified == True,  # noqa: E712
        )
        .all()
    )

    medicine_lower = medicine_name.lower()
    for rx in prescriptions:
        if rx.extracted_medicine:
            try:
                data = json.loads(rx.extracted_medicine)
                rx_med = (data.get("medicine_name") or "").lower()
                # Accept if medicine name from prescription partially matches
                if medicine_lower in rx_med or rx_med in medicine_lower:
                    logger.info(
                        f"[Safety] Verified prescription found: user={user_id} "
                        f"medicine='{medicine_name}' → rx_med='{rx_med}'"
                    )
                    return True
            except json.JSONDecodeError:
                continue

    logger.info(
        f"[Safety] No verified prescription found: user={user_id} medicine='{medicine_name}'"
    )
    return False
