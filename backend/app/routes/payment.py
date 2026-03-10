"""
routes/payment.py — Dummy payment processing endpoint.

Routes:
    POST /payment/process — Process payment for an order

Phase 1: Simulates payment success.
Phase 2: Replace with real payment gateway (Stripe/Razorpay).
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.agent import PaymentRequest, PaymentResponse
from app.services.payment_service import process_payment

router = APIRouter(prefix="/payment", tags=["Payment"])


@router.post("/process", response_model=PaymentResponse)
async def handle_payment(request: PaymentRequest, db: Session = Depends(get_db)):
    """
    Process payment for an order.

    Phase 1 simulates instant payment success.
    On success, the order status is updated to 'paid'.

    Args:
        request: Payment data (order_id, amount, payment_method)
        db: Database session

    Returns:
        PaymentResponse: Transaction ID and success status
    """
    return process_payment(db, request)
