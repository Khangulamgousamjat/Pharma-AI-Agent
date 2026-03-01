"""
services/order_service.py — Business logic for creating and querying orders.
"""

from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from typing import List
import logging

from app.models.order import Order
from app.models.medicine import Medicine
from app.models.user import User
from app.services.medicine_service import get_medicine_by_id, deduct_stock

logger = logging.getLogger(__name__)


def create_order(
    db: Session,
    user_id: int,
    medicine_id: int,
    quantity: int,
) -> Order:
    """
    Create a new order after validating stock availability.

    This function:
    1. Verifies the user exists
    2. Fetches the medicine and validates stock
    3. Deducts stock from inventory
    4. Creates the order record
    5. Commits to database

    NOTE: Prescription safety check is performed BEFORE calling this function
    in the agent tools layer. This service trusts that the agent has already
    verified prescription requirements.

    Args:
        db: Database session
        user_id: ID of the ordering user
        medicine_id: ID of the medicine to order
        quantity: Number of units to order

    Returns:
        Order: Newly created order

    Raises:
        HTTPException 400: If out of stock
        HTTPException 404: If user or medicine not found
    """
    # Validate user exists
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
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

    # Create the order record
    order = Order(
        user_id=user_id,
        medicine_id=medicine_id,
        quantity=quantity,
        total_price=total_price,
        status="confirmed",  # Auto-confirm agent-created orders
    )
    db.add(order)
    db.commit()
    db.refresh(order)

    logger.info(f"Order created: id={order.id} user={user_id} medicine={medicine.name} qty={quantity}")
    return order


def get_user_orders(db: Session, user_id: int) -> List[Order]:
    """
    Get all orders for a specific user.

    Args:
        db: Database session
        user_id: User primary key

    Returns:
        List[Order]: All orders by this user, most recent first
    """
    return (
        db.query(Order)
        .filter(Order.user_id == user_id)
        .order_by(Order.created_at.desc())
        .all()
    )


def get_all_orders(db: Session) -> List[Order]:
    """
    Get all orders in the system (admin only).

    Returns:
        List[Order]: All orders, most recent first
    """
    return db.query(Order).order_by(Order.created_at.desc()).all()
