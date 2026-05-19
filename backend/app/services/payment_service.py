"""
services/payment_service.py — Dummy payment simulation using Firestore.
"""

import uuid
import logging
from typing import Any

from app.models.order import Order
from app.models.user import User
from app.schemas.agent import PaymentRequest, PaymentResponse

logger = logging.getLogger(__name__)


def process_payment(db: Any, request: PaymentRequest) -> PaymentResponse:
    """
    Process a payment for an order (dummy implementation) in Firestore.
    """
    from fastapi import HTTPException, status

    order_doc_ref = db.collection("orders").document(request.order_id)
    order_doc = order_doc_ref.get()
    if not order_doc.exists:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Order id={request.order_id} not found.",
        )

    # Generate fake transaction ID (UUID v4)
    transaction_id = f"TXN-{uuid.uuid4().hex[:12].upper()}"

    # Update order status to paid
    order_doc_ref.update({"status": "paid"})
    order_data = order_doc.to_dict()

    logger.info(
        f"Payment processed: order={request.order_id} "
        f"amount={request.amount} method={request.payment_method} "
        f"txn={transaction_id}"
    )

    from app.agents.notification_agent import NotificationAgent
    user_doc = db.collection("users").document(order_data.get("user_id")).get()
    if user_doc.exists:
        user_data = user_doc.to_dict()
        email = user_data.get("email")
        if email:
            agent = NotificationAgent()
            agent.send_order_confirmation(email, request.order_id, order_data.get("total_price", 0.0))

    return PaymentResponse(
        status="success",
        transaction_id=transaction_id,
        message=f"Payment of ₹{request.amount:.2f} received via {request.payment_method}. Thank you!",
        order_id=request.order_id,
    )
