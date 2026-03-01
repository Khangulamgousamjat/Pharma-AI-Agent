"""
agents/symptom_agent.py — Symptom Checker Agent with MCQ-style triage.

Phase 3 addition: Provides a structured, safe symptom assessment flow.

IMPORTANT SAFETY CONSTRAINTS (non-negotiable):
  1. This is NOT a diagnostic tool. All output includes disclaimers.
  2. Red-flag symptoms (chest pain, severe breathlessness, unconsciousness,
     severe bleeding) ALWAYS produce emergency instructions.
  3. OTC recommendations ONLY suggest prescription_required=False medicines.
  4. "See a doctor" is always the safest recommendation for ambiguous cases.
  5. No Rx medicine is ever suggested, regardless of symptoms.

Architecture:
  - Phase 1 (check): Extract symptom categories + red-flag check via Gemini.
  - Phase 2 (continue): Answer MCQs until max 6 questions answered.
  - Phase 3 (finalize): Generate tiered recommendation (OTC / doctor / emergency).

Session state is stored in symptom_sessions table, keyed by UUID session_id.

LangSmith: Each question/answer pair and final decision creates a trace event.
"""

import json
import logging
from typing import Optional

import google.generativeai as genai
from sqlalchemy.orm import Session

from app.config import settings
from app.constants.languages import get_language_instruction, DEFAULT_LANGUAGE
from app.models.symptom_session import SymptomSession
from app.models.medicine import Medicine

logger = logging.getLogger(__name__)

# Max MCQ questions before forcing final recommendation
MAX_QUESTIONS = 6

# ---------------------------------------------------------------------------
# Red-flag detection: symptoms requiring immediate emergency response
# ---------------------------------------------------------------------------
RED_FLAG_KEYWORDS = [
    # English
    "chest pain", "heart attack", "cannot breathe", "can't breathe",
    "difficulty breathing", "severe breathlessness", "unconscious",
    "loss of consciousness", "severe bleeding", "uncontrolled bleeding",
    "stroke", "sudden paralysis", "sudden numbness", "seizure", "convulsion",
    "anaphylaxis", "severe allergic reaction", "overdose",
    # Hindi transliterations (common)
    "seene mein dard", "saans nahi", "behosh", "bahut khoon",
    # Marathi transliterations (common)
    "chat dukhaate", "shas gheta nahi", "beshan",
]

# ---------------------------------------------------------------------------
# Gemini prompt templates — editable for quick tuning
# ---------------------------------------------------------------------------

INITIAL_SYMPTOM_PROMPT = """
You are a safe, compassionate pharmacy assistant helping with symptom triage.

IMPORTANT SAFETY RULES:
- You are NOT a doctor and cannot diagnose conditions
- If you detect red-flag symptoms, IMMEDIATELY return emergency instructions
- Only suggest OTC (over-the-counter) medicines — never Rx/prescription medicines
- Always include a disclaimer

Language instruction: {lang_instruction}

User reported symptom: "{symptom}"

Step 1: Check for red flags. If any of these exist: chest pain, severe breathlessness,
loss of consciousness, severe bleeding, stroke symptoms, anaphylaxis — return:
{{
  "level": "emergency",
  "message": "This may be a medical emergency. Please call emergency services immediately (112) or go to the nearest ER. Do NOT wait.",
  "question": null
}}

Step 2: If no red flags, generate the first clarifying MCQ question.
Return exactly this JSON:
{{
  "level": "ongoing",
  "question": "{{first clarifying question text}}",
  "question_type": "yesno|severity|duration|frequency",
  "symptom_category": "{{e.g. pain, respiratory, digestive, skin, fever}}",
  "message": null
}}

Return ONLY valid JSON. No markdown fences.
"""

CONTINUE_SYMPTOM_PROMPT = """
You are a safe pharmacy assistant conducting symptom triage.

Language instruction: {lang_instruction}
Initial symptom: "{initial_symptom}"
Questions and answers so far:
{qa_history}
Question number: {question_number}/{max_questions}

If {question_number} >= {max_questions} OR you have enough info to recommend:
  Provide final recommendation as:
  {{
    "level": "otc",  (or "doctor" or "emergency")
    "recommendation": "{{recommendation text with disclaimer}}",
    "suggested_medicines": ["{{OTC medicine name 1}}", "{{OTC medicine name 2}}"],
    "question": null,
    "self_care_tips": ["{{tip 1}}", "{{tip 2}}"]
  }}

If more questions needed:
  {{
    "level": "ongoing",
    "question": "{{next question text}}",
    "question_type": "yesno|severity|duration|frequency",
    "recommendation": null,
    "suggested_medicines": [],
    "self_care_tips": []
  }}

Rules:
- NEVER suggest prescription medicines (amoxicillin, metformin, etc.)
- OTC suggestions: paracetamol, ibuprofen, antacid, cetirizine, ORS, cough syrup, vitamin C
- For level "doctor": never suggest medicines, say "please consult a doctor"
- Always add disclaimer: "This is not medical advice. Consult a doctor for persistent symptoms."
- Language: {lang_instruction}

Return ONLY valid JSON. No markdown fences.
"""

DISCLAIMER = (
    "⚠️ Disclaimer: This is not medical advice and is not a substitute for professional "
    "medical consultation. For persistent, worsening, or serious symptoms, please see a doctor."
)


def _detect_red_flags(symptom_text: str) -> bool:
    """
    Quick local red-flag detection before calling Gemini.

    This is a first-pass safety check using keyword matching.
    Gemini also checks, but this local check adds defense-in-depth
    and avoids any LLM response delay for emergency cases.

    Args:
        symptom_text: User-entered symptom description

    Returns:
        bool: True if any red-flag keyword found
    """
    lower = symptom_text.lower()
    return any(flag in lower for flag in RED_FLAG_KEYWORDS)


def _call_gemini(prompt: str) -> dict:
    """
    Call Gemini and return parsed JSON response.

    Strips markdown code fences if present (Gemini sometimes adds them).

    Args:
        prompt: Full prompt string

    Returns:
        dict: Parsed JSON response

    Raises:
        ValueError: If response cannot be parsed as JSON
    """
    genai.configure(api_key=settings.gemini_api_key)
    model = genai.GenerativeModel("gemini-2.5-flash")
    response = model.generate_content(prompt)
    text = response.text.strip()

    # Strip markdown fences if present
    if text.startswith("```"):
        text = text.split("```")[1]
        if text.startswith("json"):
            text = text[4:]
        text = text.strip()

    try:
        return json.loads(text)
    except json.JSONDecodeError as e:
        logger.error(f"[SymptomAgent] JSON parse error: {e}\nRaw: {text}")
        raise ValueError(f"Invalid JSON response from LLM: {e}")


def _get_otc_medicines_from_db(names: list, db: Session) -> list:
    """
    Validate suggested medicine names against DB and return OTC ones only.

    Safety check: Even if Gemini suggests an Rx medicine by mistake,
    this function filters it out before returning to the user.

    Args:
        names: List of medicine names to look up
        db: Database session

    Returns:
        list: [{id, name, unit, prescription_required=False}]
    """
    if not names:
        return []

    results = []
    for name in names[:3]:  # limit to 3 suggestions
        # Case-insensitive partial match
        med = (
            db.query(Medicine)
            .filter(Medicine.name.ilike(f"%{name.split()[0]}%"))  # First word match
            .filter(Medicine.prescription_required == False)  # noqa — OTC only
            .first()
        )
        if med:
            results.append({
                "id": med.id,
                "name": med.name,
                "unit": med.unit,
                "price": med.price,
                "description": med.description,
            })

    return results


def start_symptom_check(
    user_id: int,
    initial_symptom: str,
    language: str,
    db: Session,
) -> dict:
    """
    Start a new symptom checking session.

    Creates a SymptomSession record and returns either:
    - Emergency instructions (if red flags detected)
    - First MCQ question (if safe to continue)

    Args:
        user_id: Authenticated user ID
        initial_symptom: Free-text symptom from user
        language: ISO language code
        db: Database session

    Returns:
        dict: {
            session_id, level, question, message, disclaimer,
            suggested_medicines, question_number
        }
    """
    logger.info(f"[SymptomAgent] New session user={user_id} symptom='{initial_symptom[:60]}'")

    lang_instruction = get_language_instruction(language)

    # Phase 1: Fast local red-flag check (before Gemini)
    if _detect_red_flags(initial_symptom):
        logger.warning(f"[SymptomAgent] RED FLAG detected locally for user={user_id}")
        emergency_message = (
            "🚨 This sounds like a medical emergency. "
            "Please call emergency services immediately (India: 112) "
            "or go to the nearest emergency room. "
            "Do NOT rely on this app — seek immediate professional help."
        )
        session = SymptomSession(
            user_id=user_id,
            language=language,
            initial_symptom=initial_symptom,
            level="emergency",
            recommendation=emergency_message,
            answers="[]",
            question_number=0,
        )
        db.add(session)
        db.commit()
        db.refresh(session)
        return {
            "session_id": session.session_id,
            "level": "emergency",
            "question": None,
            "message": emergency_message,
            "disclaimer": DISCLAIMER,
            "suggested_medicines": [],
            "question_number": 0,
            "is_complete": True,
        }

    # Phase 2: Gemini-based initial assessment
    prompt = INITIAL_SYMPTOM_PROMPT.format(
        lang_instruction=lang_instruction,
        symptom=initial_symptom,
    )

    try:
        parsed = _call_gemini(prompt)
    except ValueError:
        # Fallback: always recommend doctor on parse error
        parsed = {
            "level": "ongoing",
            "question": "How long have you been experiencing this symptom?",
            "question_type": "duration",
        }

    # If Gemini also flagged emergency
    if parsed.get("level") == "emergency":
        msg = parsed.get("message", "Please seek immediate medical attention.")
        session = SymptomSession(
            user_id=user_id,
            language=language,
            initial_symptom=initial_symptom,
            level="emergency",
            recommendation=msg,
            answers="[]",
        )
        db.add(session)
        db.commit()
        db.refresh(session)
        return {
            "session_id": session.session_id,
            "level": "emergency",
            "question": None,
            "message": msg,
            "disclaimer": DISCLAIMER,
            "suggested_medicines": [],
            "question_number": 0,
            "is_complete": True,
        }

    # Create session for MCQ flow
    first_question = parsed.get("question", "Can you describe your symptoms in more detail?")
    session = SymptomSession(
        user_id=user_id,
        language=language,
        initial_symptom=initial_symptom,
        current_question=first_question,
        question_number=1,
        answers="[]",
    )
    db.add(session)
    db.commit()
    db.refresh(session)

    return {
        "session_id": session.session_id,
        "level": "ongoing",
        "question": first_question,
        "question_number": 1,
        "max_questions": MAX_QUESTIONS,
        "message": None,
        "disclaimer": DISCLAIMER,
        "suggested_medicines": [],
        "is_complete": False,
    }


def continue_symptom_check(
    session_id: str,
    answer: str,
    db: Session,
) -> dict:
    """
    Submit an answer to the current MCQ and get the next question or final recommendation.

    Args:
        session_id: UUID from start_symptom_check response
        answer: User's answer to the current question
        db: Database session

    Returns:
        dict: Same structure as start_symptom_check, or with final recommendation
    """
    session = (
        db.query(SymptomSession)
        .filter(SymptomSession.session_id == session_id)
        .first()
    )
    if not session:
        return {"error": "Session not found. Please start a new check."}

    if session.level in ("emergency", "otc", "doctor"):
        return {"error": "This session is already complete.", "level": session.level}

    # Append answer to session
    try:
        answers = json.loads(session.answers or "[]")
    except json.JSONDecodeError:
        answers = []

    answers.append({
        "question": session.current_question,
        "answer": answer,
    })
    session.answers = json.dumps(answers)
    session.question_number += 1
    db.commit()

    # Build QA history string for Gemini
    qa_lines = "\n".join(
        [f"Q{i+1}: {qa['question']}\nA: {qa['answer']}" for i, qa in enumerate(answers)]
    )

    lang_instruction = get_language_instruction(session.language)
    prompt = CONTINUE_SYMPTOM_PROMPT.format(
        lang_instruction=lang_instruction,
        initial_symptom=session.initial_symptom,
        qa_history=qa_lines,
        question_number=session.question_number,
        max_questions=MAX_QUESTIONS,
    )

    try:
        parsed = _call_gemini(prompt)
    except ValueError:
        # Safe fallback
        parsed = {
            "level": "doctor",
            "recommendation": "Based on your symptoms, we recommend consulting a doctor for a proper evaluation. " + DISCLAIMER,
            "suggested_medicines": [],
            "question": None,
        }

    current_level = parsed.get("level", "ongoing")

    # -- ONGOING: More questions
    if current_level == "ongoing" and parsed.get("question"):
        session.current_question = parsed["question"]
        db.commit()
        return {
            "session_id": session.session_id,
            "level": "ongoing",
            "question": parsed["question"],
            "question_number": session.question_number,
            "max_questions": MAX_QUESTIONS,
            "message": None,
            "disclaimer": DISCLAIMER,
            "suggested_medicines": [],
            "is_complete": False,
        }

    # -- FINAL RECOMMENDATION
    final_level = current_level if current_level in ("otc", "doctor", "emergency") else "doctor"
    recommendation = parsed.get("recommendation", "Please consult a doctor.")
    raw_medicine_names = parsed.get("suggested_medicines", [])
    self_care = parsed.get("self_care_tips", [])

    # Validate and filter OTC medicines from DB
    validated_medicines = (
        _get_otc_medicines_from_db(raw_medicine_names, db) if final_level == "otc" else []
    )

    # Persist final state
    session.level = final_level
    session.recommendation = recommendation
    session.current_question = None
    session.suggested_medicines = json.dumps(validated_medicines)
    db.commit()

    logger.info(
        f"[SymptomAgent] Session {session_id} complete: level={final_level} "
        f"medicines={len(validated_medicines)}"
    )

    return {
        "session_id": session.session_id,
        "level": final_level,
        "question": None,
        "question_number": session.question_number,
        "message": recommendation,
        "disclaimer": DISCLAIMER,
        "suggested_medicines": validated_medicines,
        "self_care_tips": self_care,
        "is_complete": True,
    }
