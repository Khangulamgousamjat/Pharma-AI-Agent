"""
routes/pharmacist.py — Pharmacist dashboard and prescription verification API.

Phase 2 addition: Endpoints for pharmacists to view and approve prescriptions.

Role-based access:
  - GET endpoints are open for Phase 2 (pharmacist UI does not have separate login)
  - POST verify requires pharmacist JWT token (role checked from token)
  - Admin users can also verify prescriptions

Endpoints:
  GET  /pharmacist/prescriptions/pending  — Queue of unverified prescriptions
  POST /pharmacist/prescriptions/{id}/verify — Approve a prescription
"""

import logging
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Header, status, Body
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.prescription import PrescriptionResponse, PharmacistVerifyRequest
from app.services.prescription_service import (
    get_pending_prescriptions,
    verify_prescription,
)
from app.utils.security import verify_token

router = APIRouter(prefix="/pharmacist", tags=["Pharmacist"])
logger = logging.getLogger(__name__)


def _get_pharmacist_from_token(authorization: str) -> dict:
    """
    Verify JWT and ensure user has pharmacist or admin role.

    Args:
        authorization: 'Bearer <token>' header value

    Returns:
        dict: Token payload (user_id, role)

    Raises:
        HTTPException 401: Missing or invalid token
        HTTPException 403: User is not a pharmacist or admin
    """
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
    description="Returns prescriptions awaiting verification, oldest first (FIFO).",
)
def get_pending_prescriptions_route(
    db: Session = Depends(get_db),
):
    """
    Pharmacist dashboard queue — returns all prescriptions not yet verified.

    Ordered oldest-first so pharmacists can process in order of submission.
    """
    pending = get_pending_prescriptions(db)
    logger.info(f"[Pharmacist] Pending prescriptions count: {len(pending)}")
    return pending


@router.post(
    "/prescriptions/{prescription_id}/verify",
    response_model=PrescriptionResponse,
    summary="Verify a prescription (pharmacist approval)",
    description="Marks prescription as verified by the authenticated pharmacist.",
)
def verify_prescription_route(
    prescription_id: int,
    request: PharmacistVerifyRequest = Body(default=PharmacistVerifyRequest()),
    authorization: str = Header(None),
    db: Session = Depends(get_db),
):
    """
    Approve a prescription after pharmacist review.

    Sets verified=True and records the pharmacist's user ID for audit trail.
    Once verified, the Safety Agent will allow Rx orders for the
    medicine listed in the prescription.

    Requires: Pharmacist or Admin JWT token in Authorization header.

    Args:
        prescription_id: ID of the prescription to verify
        request: Optional notes from the pharmacist
        authorization: 'Bearer <token>'
    """
    payload = _get_pharmacist_from_token(authorization)
    pharmacist_id = payload.get("user_id")

    logger.info(f"[Pharmacist] Verifying prescription={prescription_id} by pharmacist={pharmacist_id}")

    if request.notes:
        logger.info(f"[Pharmacist] Notes: {request.notes}")

    # verify_prescription raises 404 if not found, 400 if already verified
    updated = verify_prescription(db, prescription_id, pharmacist_id)
    return updated
