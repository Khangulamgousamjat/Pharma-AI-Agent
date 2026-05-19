"""
models/order.py — Firestore schema for the Orders collection.
"""

from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional

class OrderStatus:
    """Order status constants."""
    PENDING = "pending"
    CONFIRMED = "confirmed"
    CANCELLED = "cancelled"
    PAID = "paid"

class Order(BaseModel):
    """
    Order Firestore document schema.
    """
    id: str = Field(description="Firestore Document ID")
    user_id: str
    medicine_id: str
    quantity: int = 1
    total_price: float = 0.0
    status: str = "pending"
    created_at: datetime = Field(default_factory=datetime.utcnow)

    def to_dict(self):
        # We convert datetime to native datetime or string for firestore
        return self.model_dump(exclude={'id'})
