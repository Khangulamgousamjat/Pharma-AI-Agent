"""
services/payment_service.py — Dummy payment simulation for Phase 1.

In Phase 2, replace this with a real payment gateway integration
(Stripe, Razorpay, etc.). For now, all payments succeed immediately.
"""

import uuid
import logging
from sqlalchemy.orm import Session

from app.models.order import Order
from app.models.user import User
from app.schemas.agent import PaymentRequest, PaymentResponse

logger = logging.getLogger(__name__)


def process_payment(db: Session, request: PaymentRequest) -> PaymentResponse:
    """
    Process a payment for an order (dummy implementation).

    Simulates payment success by:
    1. Generating a fake transaction ID
    2. Updating order status to 'paid'
    3. Returning a success response

    Args:
        db: Database session
        request: Payment request (order_id, amount, payment_method)

    Returns:
        PaymentResponse: Success response with transaction ID

    Raises:
        HTTPException 404: If the order is not found
    """
    from fastapi import HTTPException, status

    # Fetch the order to update its status
    order = db.query(Order).filter(Order.id == request.order_id).first()
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Order id={request.order_id} not found.",
        )

    # Generate fake transaction ID (UUID v4)
    transaction_id = f"TXN-{uuid.uuid4().hex[:12].upper()}"

    # Update order status to paid
    order.status = "paid"
    db.commit()

    logger.info(
        f"Payment processed: order={request.order_id} "
        f"amount={request.amount} method={request.payment_method} "
        f"txn={transaction_id}"
    )

    from app.agents.notification_agent import NotificationAgent
    user = db.query(User).filter(User.id == order.user_id).first()
    if user and user.email:
        agent = NotificationAgent()
        agent.send_order_confirmation(user.email, order.id, order.total_price)

    return PaymentResponse(
        status="success",
        transaction_id=transaction_id,
        message=f"Payment of ₹{request.amount:.2f} received via {request.payment_method}. Thank you!",
        order_id=request.order_id,
    )
