"""
models/medicine.py — Firestore schema for the Medicines collection.

Tracks medicine inventory. The `prescription_required` flag is critical —
it is used by the AI agent safety logic to allow or block orders.
"""

from pydantic import BaseModel, Field
from typing import Optional

class Medicine(BaseModel):
    """
    Medicine Firestore document schema.
    """
    id: str = Field(description="Firestore Document ID")
    name: str = Field(..., description="Medicine name (e.g., 'Paracetamol 500mg')")
    stock: int = 0
    unit: str = "tablets"
    price: float = 0.0
    
    # SAFETY-CRITICAL FIELD: used by AI agent to enforce prescription logic
    prescription_required: bool = False
    
    expiry_date: Optional[str] = None # Using ISO string for Firestore dates
    description: Optional[str] = None

    def to_dict(self):
        return self.model_dump(exclude={'id'}, exclude_none=True)
