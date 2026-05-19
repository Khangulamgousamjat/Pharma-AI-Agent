"""
routes/symptom_routes.py — Symptom Checker Agent endpoints using Firestore.
"""

import logging
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from typing import List, Optional, Any

from app.firebase_db import get_db
from app.agents.symptom_agent import start_symptom_check, continue_symptom_check
from app.constants.languages import DEFAULT_LANGUAGE, SUPPORTED_LANGUAGES

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/symptom", tags=["Symptom Checker"])


class SymptomCheckRequest(BaseModel):
    user_id: str = Field(..., description="Authenticated user ID")
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
                "user_id": "user123",
                "initial_symptom": "I have a severe headache and mild fever since yesterday",
                "language": "en",
            }
        }


class SymptomContinueRequest(BaseModel):
    session_id: str = Field(..., description="UUID from /symptom/check response")
    answer: str = Field(..., min_length=1, max_length=500, description="User's MCQ answer")


class SuggestedMedicine(BaseModel):
    id: str
    name: str
    unit: str
    price: float
    description: Optional[str] = None


class SymptomResponse(BaseModel):
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


@router.post(
    "/check",
    response_model=SymptomResponse,
    summary="Start a symptom check session",
)
def symptom_check(
    request: SymptomCheckRequest,
    db: Any = Depends(get_db),
):
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
)
def symptom_continue(
    request: SymptomContinueRequest,
    db: Any = Depends(get_db),
):
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
def get_symptom_session(session_id: str, db: Any = Depends(get_db)):
    import json
    
    docs = db.collection("symptom_sessions").where("session_id", "==", session_id).limit(1).get()
    if not docs:
        raise HTTPException(status_code=404, detail="Session not found")

    session_data = docs[0].to_dict()
    
    # Parse created_at
    created_at = session_data.get("created_at")
    if created_at and hasattr(created_at, 'to_datetime'):
        created_at = created_at.to_datetime().isoformat()
    elif isinstance(created_at, str):
        pass
    else:
        created_at = None

    medicines = []
    suggested_meds = session_data.get("suggested_medicines")
    if suggested_meds:
        try:
            medicines = json.loads(suggested_meds)
        except Exception:
            medicines = []

    return {
        "session_id": session_data.get("session_id"),
        "initial_symptom": session_data.get("initial_symptom"),
        "level": session_data.get("level"),
        "recommendation": session_data.get("recommendation"),
        "suggested_medicines": medicines,
        "question_number": session_data.get("question_number"),
        "language": session_data.get("language"),
        "created_at": created_at,
    }
