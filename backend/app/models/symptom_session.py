"""
models/symptom_session.py — Firestore schema for the Symptom Sessions collection.
"""

from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional
import uuid

class SymptomSession(BaseModel):
    """
    SymptomSession Firestore document schema.
    """
    id: str = Field(description="Firestore Document ID")
    user_id: str
    session_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    language: str = "en"
    initial_symptom: str
    answers: str = "[]"  # JSON list string
    current_question: Optional[str] = None
    question_number: int = 0
    recommendation: Optional[str] = None
    level: Optional[str] = None  # otc / doctor / emergency
    suggested_medicines: Optional[str] = None  # JSON list string
    created_at: datetime = Field(default_factory=datetime.utcnow)

    def to_dict(self):
        return self.model_dump(exclude={'id'})
