"""
schemas/order.py — Pydantic schemas for Order API validation.
"""

from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional
from app.schemas.medicine import MedicineResponse


class OrderCreate(BaseModel):
    """Schema for creating an order via POST /orders/create."""
    medicine_id: int = Field(..., description="ID of the medicine to order")
    quantity: int = Field(..., ge=1, description="Quantity (must be at least 1)")


class OrderResponse(BaseModel):
    """
    Schema for order data in API responses.

    Includes nested medicine info for display.
    """
    id: int
    user_id: int
    medicine_id: int
    quantity: int
    total_price: float
    status: str
    created_at: Optional[datetime] = None
    medicine: Optional[MedicineResponse] = None

    class Config:
        from_attributes = True


class OrderStatusUpdate(BaseModel):
    """Schema for updating order status (admin use)."""
    status: str = Field(..., pattern="^(pending|confirmed|paid|cancelled)$")
