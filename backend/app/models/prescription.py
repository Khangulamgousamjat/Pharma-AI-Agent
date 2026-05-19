"""
models/prescription.py — Firestore schema for the Prescriptions collection.
"""

from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional

class Prescription(BaseModel):
    """
    Prescription Firestore document schema.
    """
    id: str = Field(description="Firestore Document ID")
    user_id: str
    image_url: str
    extracted_text: Optional[str] = None
    extracted_medicine: Optional[str] = None  # JSON string
    verified: bool = False
    verified_by: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

    def to_dict(self):
        return self.model_dump(exclude={'id'})
