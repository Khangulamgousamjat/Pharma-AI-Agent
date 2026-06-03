"""
schemas/medicine.py — Pydantic schemas for Medicine API validation.
"""

from pydantic import BaseModel, Field
from datetime import date
from typing import Optional


class MedicineResponse(BaseModel):
    """
    Schema for medicine data returned by the API.

    Includes prescription_required which drives agent safety logic.
    """
    id: int
    name: str
    stock: int
    unit: str
    price: float
    prescription_required: bool
    expiry_date: Optional[date] = None
    description: Optional[str] = None

    class Config:
        from_attributes = True


class MedicineCreate(BaseModel):
    """Schema for creating a new medicine (admin use)."""
    name: str = Field(..., min_length=2, max_length=200)
    stock: int = Field(..., ge=0, description="Stock quantity (must be >= 0)")
    unit: str = Field(default="tablets")
    price: float = Field(..., ge=0.0)
    prescription_required: bool = Field(default=False)
    expiry_date: Optional[date] = None
    description: Optional[str] = None


class MedicineUpdate(BaseModel):
    """Schema for updating medicine stock (admin use)."""
    stock: Optional[int] = Field(None, ge=0)
    price: Optional[float] = Field(None, ge=0.0)
    description: Optional[str] = None
