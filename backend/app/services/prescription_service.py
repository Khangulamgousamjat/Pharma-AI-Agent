"""
services/prescription_service.py — Business logic for prescription management using Firestore.
"""

import json
import logging
from typing import List, Optional, Any

from fastapi import HTTPException, status

from app.models.prescription import Prescription

logger = logging.getLogger(__name__)


def _doc_to_prescription(doc) -> Prescription:
    data = doc.to_dict()
    data['id'] = doc.id
    if 'created_at' in data and not isinstance(data['created_at'], str) and hasattr(data['created_at'], 'to_datetime'):
        data['created_at'] = data['created_at'].to_datetime()
    return Prescription(**data)


def create_prescription(
    db: Any,
    user_id: str,
    image_url: str,
    extracted_data: dict,
) -> Prescription:
    """
    Create a new prescription record after Vision Agent extraction.
    """
    extracted_text = extracted_data.get("raw_text", "")
    extracted_medicine = json.dumps({
        "medicine_name": extracted_data.get("medicine_name"),
        "dosage": extracted_data.get("dosage"),
        "quantity": extracted_data.get("quantity"),
        "instructions": extracted_data.get("instructions"),
        "confidence": extracted_data.get("confidence"),
    })

    presc_ref = db.collection("prescriptions").document()
    prescription = Prescription(
        id=presc_ref.id,
        user_id=user_id,
        image_url=image_url,
        extracted_text=extracted_text,
        extracted_medicine=extracted_medicine,
        verified=False,
    )
    presc_ref.set(prescription.to_dict())

    logger.info(
        f"Prescription created: id={prescription.id} user={user_id} "
        f"medicine='{extracted_data.get('medicine_name')}'"
    )
    return prescription


def get_user_prescriptions(db: Any, user_id: str) -> List[Prescription]:
    """
    Get all prescriptions uploaded by a user from Firestore.
    """
    docs = db.collection("prescriptions").where("user_id", "==", user_id).stream()
    prescriptions = [_doc_to_prescription(doc) for doc in docs]
    prescriptions.sort(key=lambda p: p.created_at, reverse=True)
    return prescriptions


def get_pending_prescriptions(db: Any) -> List[Prescription]:
    """
    Get all unverified prescriptions (pharmacist queue) from Firestore.
    """
    docs = db.collection("prescriptions").where("verified", "==", False).stream()
    prescriptions = [_doc_to_prescription(doc) for doc in docs]
    prescriptions.sort(key=lambda p: p.created_at)
    return prescriptions


def verify_prescription(
    db: Any,
    prescription_id: str,
    pharmacist_id: str,
) -> Prescription:
    """
    Mark a prescription as verified by a pharmacist in Firestore.
    """
    doc_ref = db.collection("prescriptions").document(prescription_id)
    doc = doc_ref.get()
    if not doc.exists:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Prescription id={prescription_id} not found.",
        )

    data = doc.to_dict()
    if data.get("verified"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Prescription is already verified.",
        )

    doc_ref.update({
        "verified": True,
        "verified_by": pharmacist_id
    })

    data["verified"] = True
    data["verified_by"] = pharmacist_id
    data["id"] = doc.id
    if 'created_at' in data and not isinstance(data['created_at'], str) and hasattr(data['created_at'], 'to_datetime'):
        data['created_at'] = data['created_at'].to_datetime()

    logger.info(
        f"Prescription verified: id={prescription_id} by pharmacist={pharmacist_id}"
    )
    return Prescription(**data)


def has_verified_prescription_for_medicine(
    db: Any,
    user_id: str,
    medicine_name: str,
) -> bool:
    """
    Check if a user has a verified prescription for a given medicine in Firestore.
    """
    docs = db.collection("prescriptions")\
             .where("user_id", "==", user_id)\
             .where("verified", "==", True)\
             .stream()
             
    prescriptions = [_doc_to_prescription(doc) for doc in docs]

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
