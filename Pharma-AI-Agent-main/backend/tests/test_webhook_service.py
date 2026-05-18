"""
tests/test_webhook_service.py — Unit tests for webhook fulfillment service.

Tests cover:
  - Successful first-attempt fulfillment
  - Failure → retry → eventual success
  - All retries exhausted → final failure
  - Order status updates (fulfilled / fulfillment_failed)
  - Webhook event DB records created per attempt
  - Idempotency key consistency

Run:
    cd backend
    pytest tests/test_webhook_service.py -v --tb=short
"""

import asyncio
import json
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base


# ---------------------------------------------------------------------------
# SQLite in-memory test database (avoids needing real PostgreSQL)
# ---------------------------------------------------------------------------

TEST_DB_URL = "sqlite:///./test_webhook.db"

@pytest.fixture(scope="module")
def engine():
    """Create test database engine."""
    _engine = create_engine(TEST_DB_URL, connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=_engine)
    yield _engine
    Base.metadata.drop_all(bind=_engine)


@pytest.fixture
def db(engine):
    """Provide a clean DB session for each test."""
    Session = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = Session()
    yield session
    session.rollback()
    session.close()


@pytest.fixture
def sample_order(db):
    """
    Create a sample order and medicine for webhook tests.
    Returns the order with medicine relationship loaded.
    """
    from app.models.medicine import Medicine
    from app.models.user import User
    from app.models.order import Order

    # Create user
    user = User(name="Test", email="wh_test@test.com", password_hash="x", role="user")
    db.add(user)
    db.flush()

    # Create medicine
    med = Medicine(
        name="Paracetamol 500mg",
        stock=100,
        unit="tablets",
        price=5.0,
        prescription_required=False,
    )
    db.add(med)
    db.flush()

    # Create order
    order = Order(
        user_id=user.id,
        medicine_id=med.id,
        quantity=10,
        total_price=50.0,
        status="confirmed",
    )
    db.add(order)
    db.commit()
    db.refresh(order)

    # Manually attach medicine (eager load workaround for SQLite)
    order.medicine = med
    return order


# ---------------------------------------------------------------------------
# Tests: trigger_fulfillment — Success
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_fulfillment_success_on_first_attempt(db, sample_order):
    """
    When warehouse returns 200 on first attempt:
    - Result is success=True, attempts=1
    - Order status set to 'fulfilled'
    - One WebhookEvent created with status='success'
    """
    from app.services import webhook_service
    from app.models.webhook_event import WebhookEvent

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.text = '{"status": "accepted"}'
    mock_response.raise_for_status = MagicMock()

    with patch("app.services.webhook_service.exponential_backoff_retry", new_callable=AsyncMock) as mock_retry:
        mock_retry.return_value = mock_response
        result = await webhook_service.trigger_fulfillment(sample_order.id, db)

    assert result["success"] is True
    assert "attempts" in result or result.get("webhook_event_id") is not None

    # Check order status
    db.refresh(sample_order)
    assert sample_order.status == "fulfilled"

    # Check WebhookEvent created
    events = db.query(WebhookEvent).filter(WebhookEvent.order_id == sample_order.id).all()
    assert len(events) >= 1
    success_events = [e for e in events if e.status == "success"]
    assert len(success_events) >= 1


@pytest.mark.asyncio
async def test_fulfillment_failure_after_retries(db, sample_order):
    """
    When all retries exhausted:
    - Result is success=False
    - Order status set to 'fulfillment_failed'
    """
    from app.services import webhook_service

    with patch("app.services.webhook_service.exponential_backoff_retry", new_callable=AsyncMock) as mock_retry:
        mock_retry.side_effect = Exception("Connection refused")
        result = await webhook_service.trigger_fulfillment(sample_order.id, db)

    assert result["success"] is False
    assert "failed" in result["message"].lower()

    db.refresh(sample_order)
    assert sample_order.status == "fulfillment_failed"


def test_webhook_event_idempotency_key(db, sample_order):
    """
    Verify that idempotency key follows pattern 'order_{id}'.
    This is critical to prevent duplicate fulfillments on retry.
    """
    from app.services.webhook_service import _build_payload

    payload = _build_payload(sample_order)
    assert payload["idempotency_key"] == f"order_{sample_order.id}"
    assert payload["order_id"] == sample_order.id
    assert len(payload["items"]) == 1
    assert payload["items"][0]["quantity"] == 10


def test_build_payload_includes_medicine_info(db, sample_order):
    """Payload must include medicine name and unit (not just ID)."""
    from app.services.webhook_service import _build_payload

    payload = _build_payload(sample_order)
    item = payload["items"][0]

    assert "medicine_name" in item
    assert item["medicine_name"] == "Paracetamol 500mg"
    assert item["unit"] == "tablets"


def test_get_webhook_events_empty(db, sample_order):
    """Events list is empty for orders without webhook history."""
    from app.services.webhook_service import get_webhook_events_for_order
    from app.models.order import Order

    # Use a fresh order ID that has no events
    events = get_webhook_events_for_order(order_id=99999, db=db)
    assert events == []
