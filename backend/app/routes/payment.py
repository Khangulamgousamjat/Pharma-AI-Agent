"""
routes/payment.py — Dummy payment processing endpoint using Firestore.
"""

from fastapi import APIRouter, Depends
from typing import Any

from app.firebase_db import get_db
from app.schemas.agent import PaymentRequest, PaymentResponse
from app.services.payment_service import process_payment

router = APIRouter(prefix="/payment", tags=["Payment"])


@router.post("/process", response_model=PaymentResponse)
async def handle_payment(request: PaymentRequest, db: Any = Depends(get_db)):
    """
    Process payment for an order.
    """
    return process_payment(db, request)
