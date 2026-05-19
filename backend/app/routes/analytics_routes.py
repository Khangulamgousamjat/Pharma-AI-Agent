"""
routes/analytics_routes.py — Admin analytics API endpoints using Firestore.
"""

import logging
from fastapi import APIRouter, Depends, Query
from typing import Any

from app.firebase_db import get_db
from app.services.analytics_service import (
    get_overview_stats,
    get_top_medicines,
    get_refill_stats,
    get_webhook_stats,
    get_orders_over_time,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/analytics", tags=["Analytics"])


@router.get(
    "/overview",
    summary="Get high-level KPI overview",
)
def analytics_overview(db: Any = Depends(get_db)):
    return get_overview_stats(db)


@router.get(
    "/medicines",
    summary="Get top N medicines by order volume",
)
def analytics_top_medicines(
    n: int = Query(default=10, ge=1, le=50, description="Number of top medicines"),
    db: Any = Depends(get_db),
):
    return {"medicines": get_top_medicines(db, n=n)}


@router.get(
    "/refills",
    summary="Get refill alert statistics",
)
def analytics_refills(db: Any = Depends(get_db)):
    return get_refill_stats(db)


@router.get(
    "/fulfillment",
    summary="Get webhook fulfillment statistics",
)
def analytics_fulfillment(db: Any = Depends(get_db)):
    return get_webhook_stats(db)


@router.get(
    "/orders-over-time",
    summary="Daily order counts and revenue for line chart",
)
def analytics_orders_over_time(
    days: int = Query(default=30, ge=7, le=365, description="Days to look back"),
    db: Any = Depends(get_db),
):
    return {"data": get_orders_over_time(db, days=days)}
