"""
schemas/refill.py — Pydantic schemas for Refill Alert API.

Phase 2 addition: Covers refill prediction responses and prediction trigger.
"""

from pydantic import BaseModel
from datetime import date, datetime
from typing import Optional


class RefillAlertResponse(BaseModel):
    """Schema for refill alert data returned in API responses."""
    id: int
    user_id: int
    medicine_id: int
    predicted_refill_date: Optional[date] = None
    days_supply: int
    status: str
    created_at: Optional[datetime] = None

    # Nested medicine name for display (populated by service)
    medicine_name: Optional[str] = None
    medicine_unit: Optional[str] = None

    class Config:
        from_attributes = True


class RefillPredictionRequest(BaseModel):
    """Schema for POST /refill-alerts/run-prediction."""
    user_id: int


class RefillPredictionResponse(BaseModel):
    """Response after running the refill prediction engine."""
    user_id: int
    alerts_created: int
    alerts_updated: int
    message: str
