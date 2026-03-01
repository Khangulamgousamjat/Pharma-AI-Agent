"""
models/symptom_session.py — SQLAlchemy ORM model for Symptom Checker sessions.

Phase 3 addition: Tracks a user's complete symptom triage session:
  - Initial reported symptom
  - MCQ answers given so far
  - Final recommendation (OTC / doctor / emergency)

Each POST /symptom/check creates a new session.
Each POST /symptom/continue appends to answers and may finalize.

Recommendation levels:
  otc         → suggest OTC medicines, self-care
  doctor      → non-urgent doctor visit recommended
  emergency   → red-flag detected → call emergency immediately
"""

import uuid
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class SymptomSession(Base):
    """
    SymptomSession ORM model.

    Attributes:
        id: Primary key
        user_id: FK → users.id
        session_id: UUID string (used in API to correlate requests)
        language: ISO language code (en / hi / mr)
        initial_symptom: Free-text symptom reported by user
        answers: JSON list of MCQ answer strings provided so far
        current_question: Text of the current MCQ question (None if session closed)
        question_number: 1-6, current position in MCQ flow
        recommendation: Final recommendation text (None until session resolved)
        level: 'otc' | 'doctor' | 'emergency' | None (ongoing)
        suggested_medicines: JSON list of suggested OTC medicine names (level=otc)
        created_at: Session start time
    """

    __tablename__ = "symptom_sessions"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    # UUID session identifier — sent back to client for /symptom/continue
    session_id = Column(String(36), default=lambda: str(uuid.uuid4()), unique=True, index=True)

    # Language context for multilingual responses
    language = Column(String(10), default="en", nullable=False)

    # Initial symptom text from user
    initial_symptom = Column(Text, nullable=False)

    # JSON array of answers given so far: ["Yes", "Moderate", "2 days"]
    answers = Column(Text, default="[]", nullable=False)

    # Current MCQ question text (None when resolved)
    current_question = Column(Text, nullable=True)
    question_number = Column(Integer, default=0, nullable=False)

    # Final output (populated when all questions answered)
    recommendation = Column(Text, nullable=True)
    level = Column(String(20), nullable=True)  # otc / doctor / emergency

    # Suggested OTC medicines JSON: [{"id": 1, "name": "...", "dosage": "..."}]
    suggested_medicines = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationship
    user = relationship("User", backref="symptom_sessions")

    def __repr__(self) -> str:
        return (
            f"<SymptomSession id={self.id} user={self.user_id} "
            f"level={self.level} q={self.question_number}>"
        )
