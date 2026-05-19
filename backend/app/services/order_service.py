"""
services/order_service.py — Business logic for creating and querying orders using Firestore.
"""

from fastapi import HTTPException, status
from typing import List, Any
import logging

from app.models.order import Order
from app.models.medicine import Medicine
from app.models.user import User
from app.services.medicine_service import get_medicine_by_id, deduct_stock

logger = logging.getLogger(__name__)


def create_order(
    db: Any,
    user_id: str,
    medicine_id: str,
    quantity: int,
) -> Order:
    """
    Create a new order after validating stock availability in Firestore.
    """
    # Validate user exists
    user_doc = db.collection("users").document(user_id).get()
    if not user_doc.exists:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with id={user_id} not found.",
        )

    # Fetch and validate medicine
    medicine = get_medicine_by_id(db, medicine_id)

    # Calculate total price before deducting stock
    total_price = round(medicine.price * quantity, 2)

    # Deduct stock from inventory (raises 400 if insufficient)
    deduct_stock(db, medicine, quantity)

    # Create the order record in Firestore
    order_ref = db.collection("orders").document()
    order = Order(
        id=order_ref.id,
        user_id=user_id,
        medicine_id=medicine_id,
        quantity=quantity,
        total_price=total_price,
        status="confirmed",  # Auto-confirm agent-created orders
    )
    order_ref.set(order.to_dict())

    logger.info(f"Order created: id={order.id} user={user_id} medicine={medicine.name} qty={quantity}")
    return order


def _doc_to_order(doc) -> Order:
    data = doc.to_dict()
    data['id'] = doc.id
    # Handle possible string timestamp conversion if stored as ISO string or Firebase Timestamp
    if 'created_at' in data and not isinstance(data['created_at'], str) and hasattr(data['created_at'], 'to_datetime'):
        data['created_at'] = data['created_at'].to_datetime()
    return Order(**data)


def get_user_orders(db: Any, user_id: str) -> List[Order]:
    """
    Get all orders for a specific user from Firestore.
    """
    docs = db.collection("orders").where("user_id", "==", user_id).stream()
    orders = [_doc_to_order(doc) for doc in docs]
    # Sort in memory: most recent first
    orders.sort(key=lambda o: o.created_at, reverse=True)
    return orders


def get_all_orders(db: Any) -> List[Order]:
    """
    Get all orders in the system (admin only) from Firestore.
    """
    docs = db.collection("orders").stream()
    orders = [_doc_to_order(doc) for doc in docs]
    orders.sort(key=lambda o: o.created_at, reverse=True)
    return orders
