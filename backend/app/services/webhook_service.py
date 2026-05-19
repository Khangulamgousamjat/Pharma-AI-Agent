"""
services/webhook_service.py — Fulfillment webhook automation using Firestore.
"""

import json
import logging
import asyncio
from datetime import datetime
from typing import Optional, Any

import httpx

from app.config import settings
from app.models.order import Order
from app.models.webhook_event import WebhookEvent
from app.utils.retries import exponential_backoff_retry

logger = logging.getLogger(__name__)


def _build_payload(db: Any, order: Order) -> dict:
    """
    Build the fulfillment webhook request payload from Firestore.
    """
    medicine_doc = db.collection("medicines").document(order.medicine_id).get()
    medicine_name = f"Medicine#{order.medicine_id}"
    unit = "units"
    if medicine_doc.exists:
        med_data = medicine_doc.to_dict()
        medicine_name = med_data.get("name", medicine_name)
        unit = med_data.get("unit", unit)

    return {
        "order_id": order.id,
        "user_id": order.user_id,
        "idempotency_key": f"order_{order.id}",
        "items": [
            {
                "medicine_id": order.medicine_id,
                "medicine_name": medicine_name,
                "quantity": order.quantity,
                "unit": unit,
            }
        ],
        "total_price": order.total_price,
        "status": order.status,
        "preferred_delivery_date": None,
    }


def _record_attempt(
    db: Any,
    order_id: str,
    attempt_number: int,
    status: str,
    payload: dict,
    response_body: Optional[str] = None,
    http_status_code: Optional[int] = None,
) -> WebhookEvent:
    """
    Persist a webhook attempt record in Firestore.
    """
    event_ref = db.collection("webhook_events").document()
    event = WebhookEvent(
        id=event_ref.id,
        order_id=order_id,
        attempt_number=attempt_number,
        status=status,
        idempotency_key=f"order_{order_id}",
        request_payload=json.dumps(payload),
        response_body=response_body,
        http_status_code=http_status_code,
    )
    event_ref.set(event.to_dict())
    return event


def _doc_to_order(doc) -> Order:
    data = doc.to_dict()
    data['id'] = doc.id
    if 'created_at' in data and not isinstance(data['created_at'], str) and hasattr(data['created_at'], 'to_datetime'):
        data['created_at'] = data['created_at'].to_datetime()
    return Order(**data)


def _doc_to_event(doc) -> WebhookEvent:
    data = doc.to_dict()
    data['id'] = doc.id
    if 'created_at' in data and not isinstance(data['created_at'], str) and hasattr(data['created_at'], 'to_datetime'):
        data['created_at'] = data['created_at'].to_datetime()
    return WebhookEvent(**data)


async def trigger_fulfillment(order_id: str, db: Any) -> dict:
    """
    Trigger warehouse fulfillment for an order with retry logic in Firestore.
    """
    logger.info(f"[Webhook] Starting fulfillment for order={order_id}")

    # Load order
    order_doc = db.collection("orders").document(order_id).get()
    if not order_doc.exists:
        logger.error(f"[Webhook] Order {order_id} not found")
        return {"success": False, "attempts": 0, "message": f"Order {order_id} not found"}

    order = _doc_to_order(order_doc)
    payload = _build_payload(db, order)
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
        db.collection("orders").document(order_id).update({"status": "fulfilled"})

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
        db.collection("orders").document(order_id).update({"status": "fulfillment_failed"})

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


async def retrigger_webhook(order_id: str, db: Any) -> dict:
    """
    Manually retrigger fulfillment for an order (admin action).
    """
    logger.info(f"[Webhook] Manual retrigger for order={order_id}")
    order_ref = db.collection("orders").document(order_id)
    if order_ref.get().exists:
        order_ref.update({"status": "confirmed"})
    return await trigger_fulfillment(order_id, db)


def get_webhook_events_for_order(order_id: str, db: Any) -> list:
    """
    Get all webhook attempts for a specific order in Firestore.
    """
    docs = db.collection("webhook_events").where("order_id", "==", order_id).stream()
    events = [_doc_to_event(doc) for doc in docs]
    events.sort(key=lambda e: e.created_at)
    return events
