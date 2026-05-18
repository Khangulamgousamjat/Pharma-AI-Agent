"""
services/webhook_service.py — Fulfillment webhook automation.

Phase 3 addition: When an order is confirmed, automatically notifies the
warehouse fulfillment system via HTTP POST with retry logic.

Design decisions:
  - Idempotency: every retry uses the same X-Idempotency-Key: order_{order_id}
    so the warehouse can safely ignore duplicates.
  - Retry strategy: exponential backoff with full jitter (see utils/retries.py).
    Max 5 attempts, base delay 1s → delays roughly 2, 4, 8, 16, 32s (+jitter).
  - Each attempt is recorded in webhook_events table for admin visibility.
  - On final failure: order status set to 'fulfillment_failed'.
  - On success: order status set to 'fulfilled'.

LangSmith: Every attempt is logged as a structured event for observability.
"""

import json
import logging
import asyncio
from datetime import datetime
from typing import Optional

import httpx
from sqlalchemy.orm import Session

from app.config import settings
from app.models.order import Order
from app.models.webhook_event import WebhookEvent
from app.utils.retries import exponential_backoff_retry

logger = logging.getLogger(__name__)


def _build_payload(order: Order) -> dict:
    """
    Build the fulfillment webhook request payload.

    Args:
        order: Order ORM object with medicine relationship loaded

    Returns:
        dict: Standardized fulfillment payload
    """
    medicine = order.medicine
    return {
        "order_id": order.id,
        "user_id": order.user_id,
        "idempotency_key": f"order_{order.id}",
        "items": [
            {
                "medicine_id": order.medicine_id,
                "medicine_name": medicine.name if medicine else f"Medicine#{order.medicine_id}",
                "quantity": order.quantity,
                "unit": medicine.unit if medicine else "units",
            }
        ],
        "total_price": order.total_price,
        "status": order.status,
        "preferred_delivery_date": None,  # Phase 4: delivery scheduling
    }


def _record_attempt(
    db: Session,
    order_id: int,
    attempt_number: int,
    status: str,
    payload: dict,
    response_body: Optional[str] = None,
    http_status_code: Optional[int] = None,
) -> WebhookEvent:
    """
    Persist a webhook attempt record in the database.

    Args:
        db: Database session
        order_id: Order being fulfilled
        attempt_number: 1-indexed attempt count
        status: 'pending' | 'success' | 'failed'
        payload: Request payload dict
        response_body: HTTP response body or error message
        http_status_code: HTTP status code

    Returns:
        WebhookEvent: Created/updated record
    """
    event = WebhookEvent(
        order_id=order_id,
        attempt_number=attempt_number,
        status=status,
        idempotency_key=f"order_{order_id}",
        request_payload=json.dumps(payload),
        response_body=response_body,
        http_status_code=http_status_code,
    )
    db.add(event)
    db.commit()
    db.refresh(event)
    return event


async def trigger_fulfillment(order_id: int, db: Session) -> dict:
    """
    Trigger warehouse fulfillment for an order with retry logic.

    Algorithm:
    1. Load order from DB
    2. Build payload
    3. Attempt HTTP POST to FULFILLMENT_WEBHOOK_URL with retries
    4. Record each attempt in webhook_events
    5. Update order status on final outcome (fulfilled / fulfillment_failed)

    Args:
        order_id: ID of the order to fulfill
        db: SQLAlchemy session

    Returns:
        dict: {
            "success": bool,
            "attempts": int,
            "message": str,
            "webhook_event_id": int | None
        }
    """
    logger.info(f"[Webhook] Starting fulfillment for order={order_id}")

    # Load order
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        logger.error(f"[Webhook] Order {order_id} not found")
        return {"success": False, "attempts": 0, "message": f"Order {order_id} not found"}

    payload = _build_payload(order)
    webhook_url = settings.fulfillment_webhook_url
    idempotency_key = f"order_{order_id}"

    attempt_count = 0
    last_event: Optional[WebhookEvent] = None

    async def _make_request() -> httpx.Response:
        """Single HTTP POST attempt — wrapped in retry function."""
        nonlocal attempt_count
        attempt_count += 1

        logger.info(
            f"[Webhook] Attempt {attempt_count}/{settings.webhook_max_retries} "
            f"→ {webhook_url}"
        )

        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                webhook_url,
                json=payload,
                headers={
                    "Content-Type": "application/json",
                    "X-Idempotency-Key": idempotency_key,
                    "X-Agent": "PharmaAgent-AI-v3",
                },
            )
            response.raise_for_status()
            return response

    def _on_retry(exc: Exception, attempt: int) -> None:
        """Callback invoked before each retry — records the failed attempt."""
        nonlocal last_event
        last_event = _record_attempt(
            db=db,
            order_id=order_id,
            attempt_number=attempt,
            status="failed",
            payload=payload,
            response_body=str(exc),
            http_status_code=None,
        )

    try:
        response = await exponential_backoff_retry(
            func=_make_request,
            max_retries=settings.webhook_max_retries,
            base_delay=settings.webhook_base_delay,
            on_retry=_on_retry,
        )

        # SUCCESS
        response_text = response.text[:1000]  # truncate for storage
        last_event = _record_attempt(
            db=db,
            order_id=order_id,
            attempt_number=attempt_count,
            status="success",
            payload=payload,
            response_body=response_text,
            http_status_code=response.status_code,
        )

        # Update order status to fulfilled
        order.status = "fulfilled"
        db.commit()

        logger.info(
            f"[Webhook] Fulfillment SUCCESS: order={order_id} "
            f"attempts={attempt_count} http={response.status_code}"
        )
        return {
            "success": True,
            "attempts": attempt_count,
            "message": f"Fulfillment confirmed after {attempt_count} attempt(s).",
            "webhook_event_id": last_event.id,
        }

    except Exception as e:
        # FINAL FAILURE — all retries exhausted
        last_event = _record_attempt(
            db=db,
            order_id=order_id,
            attempt_number=attempt_count,
            status="failed",
            payload=payload,
            response_body=str(e),
            http_status_code=None,
        )

        # Mark order as fulfillment_failed
        order.status = "fulfillment_failed"
        db.commit()

        logger.error(
            f"[Webhook] Fulfillment FAILED: order={order_id} "
            f"attempts={attempt_count} error={e}"
        )
        return {
            "success": False,
            "attempts": attempt_count,
            "message": f"Fulfillment failed after {attempt_count} attempt(s): {str(e)}",
            "webhook_event_id": last_event.id if last_event else None,
        }


async def retrigger_webhook(order_id: int, db: Session) -> dict:
    """
    Manually retrigger fulfillment for an order (admin action).

    Resets order status and runs the full fulfillment flow again.
    Used when warehouse was temporarily unavailable.

    Args:
        order_id: Order to retry
        db: Database session

    Returns:
        dict: Same as trigger_fulfillment
    """
    logger.info(f"[Webhook] Manual retrigger for order={order_id}")
    order = db.query(Order).filter(Order.id == order_id).first()
    if order:
        order.status = "confirmed"  # Reset to allow re-trigger
        db.commit()
    return await trigger_fulfillment(order_id, db)


def get_webhook_events_for_order(order_id: int, db: Session) -> list:
    """
    Get all webhook attempts for a specific order.

    Args:
        order_id: Order ID
        db: Database session

    Returns:
        List[WebhookEvent]: All attempts, oldest first
    """
    return (
        db.query(WebhookEvent)
        .filter(WebhookEvent.order_id == order_id)
        .order_by(WebhookEvent.created_at.asc())
        .all()
    )
