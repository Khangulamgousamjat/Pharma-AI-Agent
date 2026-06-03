"""
services/medicine_service.py — Business logic for medicine inventory queries using Firestore.
"""

from fastapi import HTTPException, status
from typing import List, Optional
import logging
from firebase_admin import firestore

from app.models.medicine import Medicine

logger = logging.getLogger(__name__)


def _doc_to_medicine(doc) -> Medicine:
    """Helper to convert Firestore DocumentSnapshot to Medicine model."""
    data = doc.to_dict()
    data['id'] = doc.id
    return Medicine(**data)


def get_all_medicines(db: firestore.Client) -> List[Medicine]:
    """
    Retrieve all medicines from the inventory.
    """
    docs = db.collection('medicines').order_by('name').stream()
    return [_doc_to_medicine(doc) for doc in docs]


def get_medicine_by_id(db: firestore.Client, medicine_id: str) -> Medicine:
    """
    Retrieve a single medicine by its document ID.
    """
    doc_ref = db.collection('medicines').document(medicine_id)
    doc = doc_ref.get()
    
    if not doc.exists:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Medicine with id={medicine_id} not found.",
        )
    return _doc_to_medicine(doc)


def search_medicines(db: firestore.Client, query: str) -> List[Medicine]:
    """
    Search medicines by name. 
    Note: Firestore doesn't support partial ILIKE matching natively.
    For small datasets, we fetch all and filter in memory. For large datasets, 
    consider Algolia/Typesense or a prefix search.
    """
    query_lower = query.lower()
    docs = db.collection('medicines').stream()
    
    results = []
    for doc in docs:
        med = _doc_to_medicine(doc)
        if query_lower in med.name.lower():
            results.append(med)
            
    # Sort by name as in original logic
    results.sort(key=lambda x: x.name)
    return results


def find_medicine_by_name(db: firestore.Client, name: str) -> Optional[Medicine]:
    """
    Find a medicine by approximate name match (used by AI agent).
    """
    results = search_medicines(db, name)
    if results:
        return results[0]
    return None


def deduct_stock(db: firestore.Client, medicine: Medicine, quantity: int) -> Medicine:
    """
    Deduct ordered quantity from medicine stock using Firestore transactions to prevent race conditions.
    """
    transaction = db.transaction()
    doc_ref = db.collection('medicines').document(medicine.id)
    
    @firestore.transactional
    def update_in_transaction(transaction, doc_ref, quantity):
        snapshot = doc_ref.get(transaction=transaction)
        if not snapshot.exists:
             raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Medicine not found.",
            )
             
        current_stock = snapshot.get('stock')
        if current_stock < quantity:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Insufficient stock. Available: {current_stock}.",
            )
            
        new_stock = current_stock - quantity
        transaction.update(doc_ref, {'stock': new_stock})
        return new_stock
        
    try:
        new_stock = update_in_transaction(transaction, doc_ref, quantity)
        medicine.stock = new_stock
        logger.info(f"Stock deducted: {medicine.name} by {quantity} units. Remaining: {medicine.stock}")
        return medicine
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        logger.error(f"Failed to deduct stock: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update stock due to an internal error."
        )
