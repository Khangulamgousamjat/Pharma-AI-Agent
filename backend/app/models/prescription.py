"""
models/prescription.py — SQLAlchemy ORM model for the Prescriptions table.

Phase 2 addition: Tracks prescription images uploaded by users.

Workflow:
  1. User uploads a prescription image via POST /prescriptions/upload
  2. Vision Agent (Gemini Vision) extracts medicine names, dosage, quantity
  3. Record is saved as verified=False (pending pharmacist review)
  4. Pharmacist reviews via /pharmacist/prescriptions/pending
  5. Pharmacist POSTs verify → verified=True, verified_by=pharmacist_id
  6. Safety Agent now allows Rx orders for this user for that medicine
"""

from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class Prescription(Base):
    """
    Prescription ORM model.

    Attributes:
        id: Primary key
        user_id: FK → users.id — patient who uploaded the prescription
        image_url: Local path to the saved prescription image file
        extracted_text: Raw OCR/Vision text extracted from the image
        extracted_medicine: Medicine name extracted by Vision Agent (JSON string)
        verified: True once a pharmacist has approved this prescription
        verified_by: FK → users.id — pharmacist who approved (nullable until verified)
        created_at: Upload timestamp
    """

    __tablename__ = "prescriptions"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    # Image storage — local file path (Phase 2: local; Phase 3: cloud storage)
    image_url = Column(String(500), nullable=False)

    # Vision Agent output — raw text from image analysis
    extracted_text = Column(Text, nullable=True)

    # Structured extraction — JSON string: {"medicine_name": ..., "dosage": ..., "quantity": ...}
    extracted_medicine = Column(Text, nullable=True)

    # Verification status — pharmacist must set verified=True before Rx orders are allowed
    verified = Column(Boolean, default=False, nullable=False)
    verified_by = Column(Integer, ForeignKey("users.id"), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    user = relationship("User", foreign_keys=[user_id], backref="prescriptions")
    pharmacist = relationship("User", foreign_keys=[verified_by])

    def __repr__(self) -> str:
        return f"<Prescription id={self.id} user={self.user_id} verified={self.verified}>"
