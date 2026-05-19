"""
models/refill_alert.py — Firestore schema for the Refill Alerts collection.
"""

from pydantic import BaseModel, Field
from datetime import datetime, date
from typing import Optional

class RefillAlert(BaseModel):
    """
    RefillAlert Firestore document schema.
    """
    id: str = Field(description="Firestore Document ID")
    user_id: str
    medicine_id: str
    predicted_refill_date: Optional[str] = None  # Using ISO date string (YYYY-MM-DD)
    days_supply: int = 30
    status: str = "pending"  # pending, notified, ordered
    created_at: datetime = Field(default_factory=datetime.utcnow)

    def to_dict(self):
        return self.model_dump(exclude={'id'})
