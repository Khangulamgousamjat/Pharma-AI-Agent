"""
schemas/prescription.py — Pydantic schemas for Prescription API.

Phase 2 addition: Covers prescription upload, response, and pharmacist verification.
"""

from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional


class PrescriptionResponse(BaseModel):
    """Schema for prescription data returned in API responses."""
    id: int
    user_id: int
    image_url: str
    extracted_text: Optional[str] = None
    extracted_medicine: Optional[str] = None  # JSON string of extracted detail
    verified: bool
    verified_by: Optional[int] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class PrescriptionUploadResponse(BaseModel):
    """
    Response returned after a prescription image is uploaded and processed.

    Includes extracted medicine data from the Vision Agent.
    """
    prescription_id: int
    message: str
    extracted: dict  # {medicine_name, dosage, quantity, raw_text}
    verified: bool = False


class PharmacistVerifyRequest(BaseModel):
    """Schema for POST /pharmacist/prescriptions/{id}/verify."""
    notes: Optional[str] = Field(None, description="Optional pharmacist notes")


class ExtractedMedicineData(BaseModel):
    """Structured data extracted from a prescription image by the Vision Agent."""
    medicine_name: Optional[str] = None
    dosage: Optional[str] = None
    quantity: Optional[int] = None
    raw_text: Optional[str] = None
    confidence: Optional[str] = None  # 'high', 'medium', 'low'
