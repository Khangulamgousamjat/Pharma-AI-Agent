"""
routes/webhook_routes.py — Webhook fulfillment and simulation endpoints.

Phase 3 addition:
  - POST /webhook/simulate   — mock warehouse endpoint (local dev only)
  - POST /webhook/retrigger/{order_id} — admin: manually retry fulfillment
  - GET  /webhook/events/{order_id}    — view all attempts for an order

The /simulate endpoint mimics a real warehouse API. It returns:
  - Success (200) 80% of the time
  - Failure (503) 20% of the time (for retry testing)

Admin can toggle failure behavior via ?force_fail=true query param.
"""

import logging
import random
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional, Annotated

from app.database import SessionLocal, get_db
from app.services.webhook_service import (
    retrigger_webhook,
    get_webhook_events_for_order,
)
from app.utils.security import verify_token

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/webhook", tags=["Webhook"])



# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------

class FulfillmentPayload(BaseModel):
    """Payload sent by warehouse webhook trigger."""
    order_id: int
    user_id: int
    items: list
    total_price: float
    idempotency_key: Optional[str] = None


class WebhookEventOut(BaseModel):
    id: int
    order_id: int
    attempt_number: int
    status: str
    idempotency_key: Optional[str] = None
    http_status_code: Optional[int] = None
    response_body: Optional[str] = None
    created_at: Optional[str] = None

    class Config:
        from_attributes = True


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@router.post(
    "/simulate",
    summary="Mock warehouse fulfillment endpoint (local dev only)",
    description=(
        "Simulates a real fulfillment warehouse API. Succeeds 80% of the time. "
        "Pass ?force_fail=true to always return 503 (for retry testing). "
        "This endpoint should NOT be used in production."
    ),
    status_code=200,
)
async def simulate_warehouse(
    payload: FulfillmentPayload,
    force_fail: bool = Query(default=False, description="Force failure for retry testing"),
):
    """
    Mock warehouse fulfillment endpoint.

    The idempotency key in headers ensures duplicate requests (from retries)
    are safely ignored by returning the same success response.

    Args:
        payload: Order fulfillment payload
        force_fail: If True, always returns 503

    Returns:
        dict: Fulfillment acknowledgment or error
    """
    idempotency_key = payload.idempotency_key or f"order_{payload.order_id}"

    # Simulate failure if requested or randomly (20% chance)
    if force_fail or random.random() < 0.2:
        logger.info(
            f"[WebhookSimulate] Simulating FAILURE for order={payload.order_id} "
            f"idempotency_key={idempotency_key}"
        )
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Warehouse temporarily unavailable. Please retry.",
        )

    # Simulate success
    logger.info(
        f"[WebhookSimulate] Simulating SUCCESS for order={payload.order_id} "
        f"items={len(payload.items)}"
    )
    return {
        "status": "accepted",
        "fulfillment_id": f"FUL-{payload.order_id:06d}",
        "order_id": payload.order_id,
        "idempotency_key": idempotency_key,
        "message": "Order accepted for fulfillment. Estimated dispatch: 24h.",
        "estimated_delivery": "2-3 business days",
    }


@router.post(
    "/retrigger/{order_id}",
    summary="Manually retry fulfillment for an order (admin only)",
    description=(
        "Re-triggers webhook fulfillment for an order that previously failed. "
        "Resets order status and runs full retry flow. Admin JWT required."
    ),
)
async def retrigger_order(
    order_id: int,
    db: Annotated[Session, Depends(get_db)],
):
    """
    Admin action: retry fulfillment webhook for a failed order.

    This is useful when the warehouse was temporarily down and orders
    are stuck in 'fulfillment_failed' status.

    Args:
        order_id: Order to retry
        db: Database session

    Returns:
        dict: Fulfillment result with attempt count and success status
    """
    logger.info(f"[WebhookRoute] Admin retrigger for order={order_id}")
    result = await retrigger_webhook(order_id=order_id, db=db)

    if not result["success"]:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=result["message"],
        )

    return result


@router.get(
    "/events/{order_id}",
    response_model=List[WebhookEventOut],
    summary="Get all webhook attempts for an order",
)
def get_webhook_events(order_id: int, db: Annotated[Session, Depends(get_db)]):
    """
    Retrieve the complete webhook attempt history for a specific order.

    Shows all attempts (initial + retries) with timestamps, HTTP status codes,
    and response bodies. Used in Admin Analytics dashboard.
    """
    events = get_webhook_events_for_order(order_id=order_id, db=db)
    return [
        WebhookEventOut(
            id=e.id,
            order_id=e.order_id,
            attempt_number=e.attempt_number,
            status=e.status,
            idempotency_key=e.idempotency_key,
            http_status_code=e.http_status_code,
            response_body=(e.response_body or "")[:500],  # truncate for API response
            created_at=e.created_at.isoformat() if e.created_at else None,
        )
        for e in events
    ]
