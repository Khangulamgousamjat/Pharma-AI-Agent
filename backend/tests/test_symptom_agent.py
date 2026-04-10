"""
tests/test_symptom_agent.py — Unit tests for Symptom Checker Agent.

Tests cover:
  - Red-flag local detection (keyword matching)
  - Emergency response when red flags detected
  - OTC recommendation (non-red-flag, all MCQs answered)
  - Doctor referral recommendation
  - Session creation and persistence
  - OTC medicine validation (only prescription_required=False allowed)

Run:
    cd backend
    pytest tests/test_symptom_agent.py -v --tb=short
"""

import json
import pytest
from unittest.mock import patch, MagicMock
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base


# ---------------------------------------------------------------------------
# DB fixtures
# ---------------------------------------------------------------------------

TEST_DB_URL = "sqlite:///./test_symptom.db"


@pytest.fixture(scope="module")
def engine():
    _engine = create_engine(TEST_DB_URL, connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=_engine)
    yield _engine
    Base.metadata.drop_all(bind=_engine)


@pytest.fixture
def db(engine):
    Session = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = Session()
    yield session
    session.rollback()
    session.close()


@pytest.fixture
def db_with_user(db):
    """Create a test user for symptom session."""
    from app.models.user import User
    user = User(name="Patient", email="patient@test.com", password_hash="x", role="user")
    db.add(user)
    db.flush()
    return db, user


@pytest.fixture
def db_with_otc_medicines(db_with_user):
    """Add sample OTC and Rx medicines to test DB."""
    from app.models.medicine import Medicine
    db, user = db_with_user

    otc = Medicine(
        name="Paracetamol 500mg",
        stock=100,
        unit="tablets",
        price=5.0,
        prescription_required=False,
        description="Fever and pain relief",
    )
    rx = Medicine(
        name="Amoxicillin 500mg",
        stock=50,
        unit="capsules",
        price=25.0,
        prescription_required=True,
    )
    db.add(otc)
    db.add(rx)
    db.commit()
    return db, user


# ---------------------------------------------------------------------------
# Tests: Red-flag detection
# ---------------------------------------------------------------------------

def test_red_flag_detection_chest_pain():
    """
    Red flag keywords like 'chest pain' must be detected locally.
    This is the zero-latency safety check before any LLM call.
    """
    from app.agents.symptom_agent import _detect_red_flags

    assert _detect_red_flags("I have severe chest pain") is True
    assert _detect_red_flags("Cannot breathe at all") is True
    assert _detect_red_flags("I feel unconscious sometimes") is True
    assert _detect_red_flags("severe bleeding from my arm") is True


def test_no_red_flag_for_normal_symptoms():
    """Common non-emergency symptoms should not trigger red flags."""
    from app.agents.symptom_agent import _detect_red_flags

    assert _detect_red_flags("I have a headache since yesterday") is False
    assert _detect_red_flags("mild fever and runny nose") is False
    assert _detect_red_flags("stomach ache after eating") is False


# ---------------------------------------------------------------------------
# Tests: Emergency response session
# ---------------------------------------------------------------------------

def test_emergency_response_for_chest_pain(db_with_user):
    """
    Chest pain symptom must immediately create an emergency session.
    No MCQ questions should be asked — immediate escalation.
    """
    from app.agents.symptom_agent import start_symptom_check
    from app.models.symptom_session import SymptomSession

    db, user = db_with_user

    result = start_symptom_check(
        user_id=user.id,
        initial_symptom="I have severe chest pain and cannot breathe",
        language="en",
        db=db,
    )

    # Must be emergency, no question
    assert result["level"] == "emergency"
    assert result["question"] is None
    assert result["is_complete"] is True
    assert "emergency" in result["message"].lower() or "112" in result["message"]

    # Session saved in DB with emergency level
    session = db.query(SymptomSession).filter(
        SymptomSession.user_id == user.id,
        SymptomSession.level == "emergency"
    ).first()
    assert session is not None


# ---------------------------------------------------------------------------
# Tests: Normal MCQ flow
# ---------------------------------------------------------------------------

def test_start_check_returns_session_and_question(db_with_user):
    """
    A non-emergency symptom should create a session with a question.
    """
    from app.agents.symptom_agent import start_symptom_check
    from app.models.symptom_session import SymptomSession

    db, user = db_with_user

    # Mock Gemini to return a valid question
    mock_gemini_response = {
        "level": "ongoing",
        "question": "How long have you had this headache?",
        "question_type": "duration",
    }

    with patch("app.agents.symptom_agent._call_gemini", return_value=mock_gemini_response):
        result = start_symptom_check(
            user_id=user.id,
            initial_symptom="I have a mild headache",
            language="en",
            db=db,
        )

    assert result["level"] == "ongoing"
    assert result["question"] is not None
    assert result["question_number"] == 1
    assert result["is_complete"] is False
    assert result["session_id"] is not None

    # Session created in DB
    session = db.query(SymptomSession).filter(
        SymptomSession.session_id == result["session_id"]
    ).first()
    assert session is not None
    assert session.question_number == 1


def test_continue_check_leads_to_otc_recommendation(db_with_user):
    """
    Answering all MCQ questions with mild symptoms should produce OTC recommendation.
    Gemini is mocked to return directly to an OTC recommendation.
    """
    from app.agents.symptom_agent import start_symptom_check, continue_symptom_check
    from app.models.symptom_session import SymptomSession

    db, user = db_with_user

    # Start session
    start_mock = {
        "level": "ongoing",
        "question": "How severe is your headache on a scale of 1-10?",
        "question_type": "severity",
    }
    with patch("app.agents.symptom_agent._call_gemini", return_value=start_mock):
        start_result = start_symptom_check(
            user_id=user.id,
            initial_symptom="I have a mild headache",
            language="en",
            db=db,
        )

    session_id = start_result["session_id"]

    # Continue session — mock OTC recommendation
    otc_mock = {
        "level": "otc",
        "recommendation": "Your symptoms suggest a tension headache. Paracetamol may help. " +
                         "Disclaimer: This is not medical advice.",
        "suggested_medicines": ["Paracetamol"],
        "self_care_tips": ["Rest", "Drink water", "Avoid screen time"],
        "question": None,
    }
    with patch("app.agents.symptom_agent._call_gemini", return_value=otc_mock):
        result = continue_symptom_check(
            session_id=session_id,
            answer="3",
            db=db,
        )

    assert result["level"] == "otc"
    assert result["is_complete"] is True
    assert result["disclaimer"] is not None
    assert isinstance(result["self_care_tips"], list)


def test_otc_filter_blocks_rx_medicines(db_with_otc_medicines):
    """
    Safety check: Even if Gemini suggests an Rx medicine,
    _get_otc_medicines_from_db must filter it out.
    """
    from app.agents.symptom_agent import _get_otc_medicines_from_db

    db, user = db_with_otc_medicines

    # Request both OTC and Rx by name
    results = _get_otc_medicines_from_db(["Paracetamol", "Amoxicillin"], db)

    # Only Paracetamol (OTC) should be returned
    names = [r["name"] for r in results]
    assert any("Paracetamol" in n for n in names)
    assert not any("Amoxicillin" in n for n in names)


def test_continue_invalid_session():
    """Continuing with an invalid session_id returns an error."""
    # We can test this at the function level without DB
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker

    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    db = Session()

    from app.agents.symptom_agent import continue_symptom_check

    result = continue_symptom_check(
        session_id="non-existent-uuid",
        answer="yes",
        db=db,
    )

    assert "error" in result
    db.close()
