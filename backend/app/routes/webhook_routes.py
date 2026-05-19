"""
routes/webhook_routes.py — Webhook fulfillment and simulation endpoints using Firestore.
"""

import logging
import random
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from typing import List, Optional, Any

from app.firebase_db import get_db
from app.services.webhook_service import (
    retrigger_webhook,
    get_webhook_events_for_order,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/webhook", tags=["Webhook"])


class FulfillmentPayload(BaseModel):
    order_id: str
    user_id: str
    items: list
    total_price: float
    idempotency_key: Optional[str] = None


class WebhookEventOut(BaseModel):
    id: str
    order_id: str
    attempt_number: int
    status: str
    idempotency_key: Optional[str] = None
    http_status_code: Optional[int] = None
    response_body: Optional[str] = None
    created_at: Optional[str] = None


@router.post(
    "/simulate",
    summary="Mock warehouse fulfillment endpoint (local dev only)",
    status_code=200,
)
async def simulate_warehouse(
    payload: FulfillmentPayload,
    force_fail: bool = Query(default=False, description="Force failure for retry testing"),
):
    idempotency_key = payload.idempotency_key or f"order_{payload.order_id}"

    if force_fail or random.random() < 0.2:
        logger.info(
            f"[WebhookSimulate] Simulating FAILURE for order={payload.order_id} "
            f"idempotency_key={idempotency_key}"
        )
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Warehouse temporarily unavailable. Please retry.",
        )

    logger.info(
        f"[WebhookSimulate] Simulating SUCCESS for order={payload.order_id} "
        f"items={len(payload.items)}"
    )
    return {
        "status": "accepted",
        "fulfillment_id": f"FUL-{payload.order_id}",
        "order_id": payload.order_id,
        "idempotency_key": idempotency_key,
        "message": "Order accepted for fulfillment. Estimated dispatch: 24h.",
        "estimated_delivery": "2-3 business days",
    }


@router.post(
    "/retrigger/{order_id}",
    summary="Manually retry fulfillment for an order (admin only)",
)
async def retrigger_order(
    order_id: str,
    db: Any = Depends(get_db),
):
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
def get_webhook_events(order_id: str, db: Any = Depends(get_db)):
    events = get_webhook_events_for_order(order_id=order_id, db=db)
    
    out = []
    for e in events:
        created_at = e.created_at
        if created_at and hasattr(created_at, 'to_datetime'):
            created_at = created_at.to_datetime().isoformat()
        elif isinstance(created_at, str):
            pass
        else:
            created_at = None
            
        out.append(WebhookEventOut(
            id=e.id,
            order_id=e.order_id,
            attempt_number=e.attempt_number,
            status=e.status,
            idempotency_key=e.idempotency_key,
            http_status_code=e.http_status_code,
            response_body=(e.response_body or "")[:500],
            created_at=created_at,
        ))
    return out
