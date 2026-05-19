"""
routes/pharmacist.py — Pharmacist dashboard and prescription verification API using Firestore.
"""

import logging
from typing import List, Any

from fastapi import APIRouter, Depends, HTTPException, Header, status, Body

from app.firebase_db import get_db
from app.schemas.prescription import PrescriptionResponse, PharmacistVerifyRequest
from app.services.prescription_service import (
    get_pending_prescriptions,
    verify_prescription,
)
from app.utils.security import verify_token

router = APIRouter(prefix="/pharmacist", tags=["Pharmacist"])
logger = logging.getLogger(__name__)


def _get_pharmacist_from_token(authorization: str) -> dict:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization header with Bearer token required.",
        )
    token = authorization[7:]
    payload = verify_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token.",
        )
    role = payload.get("role", "user")
    if role not in ("pharmacist", "admin"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Access denied. Pharmacist or admin role required. Your role: {role}",
        )
    return payload


@router.get(
    "/prescriptions/pending",
    response_model=List[PrescriptionResponse],
    summary="Get all unverified prescriptions (pharmacist queue)",
)
def get_pending_prescriptions_route(
    db: Any = Depends(get_db),
):
    pending = get_pending_prescriptions(db)
    logger.info(f"[Pharmacist] Pending prescriptions count: {len(pending)}")
    return pending


@router.post(
    "/prescriptions/{prescription_id}/verify",
    response_model=PrescriptionResponse,
    summary="Verify a prescription (pharmacist approval)",
)
def verify_prescription_route(
    prescription_id: str,
    request: PharmacistVerifyRequest = Body(default=PharmacistVerifyRequest()),
    authorization: str = Header(None),
    db: Any = Depends(get_db),
):
    payload = _get_pharmacist_from_token(authorization)
    pharmacist_id = payload.get("user_id")

    logger.info(f"[Pharmacist] Verifying prescription={prescription_id} by pharmacist={pharmacist_id}")

    if request.notes:
        logger.info(f"[Pharmacist] Notes: {request.notes}")

    updated = verify_prescription(db, prescription_id, pharmacist_id)
    return updated
