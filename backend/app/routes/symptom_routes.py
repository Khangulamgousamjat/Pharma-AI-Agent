"""
routes/symptom_routes.py — Symptom Checker Agent endpoints.

Phase 3 addition: Stateful MCQ symptom triage flow.

Flow:
  1. POST /symptom/check   — start session with initial symptom
  2. POST /symptom/continue — submit MCQ answers (up to 6 times)
  3. Final response includes recommendation level + OTC medicine suggestions

Session state is stored in symptom_sessions DB table.
Each session has a UUID for stateless client correlation.

Safety: All responses include disclaimers and emergency escalation.
"""

import logging
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from typing import List, Optional, Any

from app.database import SessionLocal, get_db
from app.agents.symptom_agent import start_symptom_check, continue_symptom_check
from app.constants.languages import DEFAULT_LANGUAGE, SUPPORTED_LANGUAGES

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/symptom", tags=["Symptom Checker"])



# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------

class SymptomCheckRequest(BaseModel):
    """Start a new symptom check session."""
    user_id: int = Field(..., description="Authenticated user ID")
    initial_symptom: str = Field(
        ...,
        min_length=3,
        max_length=1000,
        description="User-reported symptom in natural language",
    )
    language: str = Field(default=DEFAULT_LANGUAGE, description="ISO language: en|hi|mr")

    class Config:
        json_schema_extra = {
            "example": {
                "user_id": 1,
                "initial_symptom": "I have a severe headache and mild fever since yesterday",
                "language": "en",
            }
        }


class SymptomContinueRequest(BaseModel):
    """Submit an MCQ answer and get next question or recommendation."""
    session_id: str = Field(..., description="UUID from /symptom/check response")
    answer: str = Field(..., min_length=1, max_length=500, description="User's MCQ answer")


class SuggestedMedicine(BaseModel):
    id: int
    name: str
    unit: str
    price: float
    description: Optional[str] = None


class SymptomResponse(BaseModel):
    """Unified response for both check and continue endpoints."""
    session_id: str
    level: str  # ongoing | otc | doctor | emergency
    question: Optional[str] = None
    question_number: int = 0
    max_questions: int = 6
    message: Optional[str] = None
    disclaimer: str
    suggested_medicines: List[Any] = []
    self_care_tips: List[str] = []
    is_complete: bool = False
    error: Optional[str] = None


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@router.post(
    "/check",
    response_model=SymptomResponse,
    summary="Start a symptom check session",
    description=(
        "Begin a new symptom checking session. Returns first MCQ question "
        "or immediate emergency instructions if red-flag symptoms detected."
    ),
)
def symptom_check(
    request: SymptomCheckRequest,
    db: Session = Depends(get_db),
):
    """
    Initialize symptom triage session.

    Creates a DB-backed session (SymptomSession) and returns either:
    - Emergency response (immediate, no questions) for red-flag symptoms
    - First clarifying MCQ question

    SAFETY: Red-flag detection runs BEFORE calling Gemini for zero-latency
    emergency escalation.
    """
    language = request.language if request.language in SUPPORTED_LANGUAGES else DEFAULT_LANGUAGE

    try:
        result = start_symptom_check(
            user_id=request.user_id,
            initial_symptom=request.initial_symptom,
            language=language,
            db=db,
        )
        return SymptomResponse(**result)
    except Exception as e:
        logger.error(f"[SymptomRoute] Check failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Symptom check failed. Please try again.",
        )


@router.post(
    "/continue",
    response_model=SymptomResponse,
    summary="Submit MCQ answer and get next question or recommendation",
    description=(
        "Submit user's answer to the current MCQ question. "
        "Returns next question or final recommendation with optional OTC medicine suggestions."
    ),
)
def symptom_continue(
    request: SymptomContinueRequest,
    db: Session = Depends(get_db),
):
    """
    Process MCQ answer and advance symptom session.

    Loads the session by UUID, appends the answer, then either:
    - Returns next question (if < MAX_QUESTIONS answered)
    - Returns final recommendation (OTC / doctor / emergency)
    """
    try:
        result = continue_symptom_check(
            session_id=request.session_id,
            answer=request.answer,
            db=db,
        )

        if "error" in result:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result["error"],
            )

        return SymptomResponse(**result)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[SymptomRoute] Continue failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not process answer. Please try again.",
        )


@router.get(
    "/session/{session_id}",
    summary="Get completed symptom session summary",
)
def get_symptom_session(session_id: str, db: Session = Depends(get_db)):
    """
    Retrieve a completed symptom session by UUID.

    Useful for displaying history or resuming a session display.
    """
    from app.models.symptom_session import SymptomSession
    import json

    session = (
        db.query(SymptomSession)
        .filter(SymptomSession.session_id == session_id)
        .first()
    )
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    medicines = []
    if session.suggested_medicines:
        try:
            medicines = json.loads(session.suggested_medicines)
        except Exception:
            medicines = []

    return {
        "session_id": session.session_id,
        "initial_symptom": session.initial_symptom,
        "level": session.level,
        "recommendation": session.recommendation,
        "suggested_medicines": medicines,
        "question_number": session.question_number,
        "language": session.language,
        "created_at": session.created_at.isoformat() if session.created_at else None,
    }
