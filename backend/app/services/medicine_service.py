"""
services/medicine_service.py — Business logic for medicine inventory queries.
"""

from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from typing import List, Optional
import logging

from app.models.medicine import Medicine

logger = logging.getLogger(__name__)


def get_all_medicines(db: Session) -> List[Medicine]:
    """
    Retrieve all medicines from the inventory.

    Args:
        db: Database session

    Returns:
        List[Medicine]: All medicine records
    """
    return db.query(Medicine).order_by(Medicine.name).all()


def get_medicine_by_id(db: Session, medicine_id: int) -> Medicine:
    """
    Retrieve a single medicine by its ID.

    Args:
        db: Database session
        medicine_id: Medicine primary key

    Returns:
        Medicine: Medicine object

    Raises:
        HTTPException 404: If medicine not found
    """
    medicine = db.query(Medicine).filter(Medicine.id == medicine_id).first()
    if not medicine:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Medicine with id={medicine_id} not found.",
        )
    return medicine


def search_medicines(db: Session, query: str) -> List[Medicine]:
    """
    Search medicines by name (case-insensitive, partial match).

    Args:
        db: Database session
        query: Search term

    Returns:
        List[Medicine]: Matching medicines
    """
    return (
        db.query(Medicine)
        .filter(Medicine.name.ilike(f"%{query}%"))
        .order_by(Medicine.name)
        .all()
    )


def find_medicine_by_name(db: Session, name: str) -> Optional[Medicine]:
    """
    Find a medicine by approximate name match (used by AI agent).

    Args:
        db: Database session
        name: Medicine name to search for

    Returns:
        Medicine | None: First matching medicine or None
    """
    return (
        db.query(Medicine)
        .filter(Medicine.name.ilike(f"%{name}%"))
        .first()
    )


def deduct_stock(db: Session, medicine: Medicine, quantity: int) -> Medicine:
    """
    Deduct ordered quantity from medicine stock.

    Args:
        db: Database session
        medicine: Medicine record to update
        quantity: Units to deduct

    Returns:
        Medicine: Updated medicine object

    Raises:
        HTTPException 400: If insufficient stock
    """
    if medicine.stock < quantity:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Insufficient stock. Available: {medicine.stock} {medicine.unit}(s).",
        )
    medicine.stock -= quantity
    db.commit()
    db.refresh(medicine)
    logger.info(f"Stock deducted: {medicine.name} by {quantity} units. Remaining: {medicine.stock}")
    return medicine
