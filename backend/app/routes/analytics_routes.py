"""
routes/analytics_routes.py — Admin analytics API endpoints.

Phase 3 addition: Provides aggregated KPI data for the admin dashboard.

All endpoints return pre-computed metrics from analytics_service.py.
These are read-only queries — no state is modified.

Access: Currently open (for demo). In production, add JWT admin check.
"""

import logging
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import List, Annotated

from app.database import SessionLocal, get_db
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
    description="Returns total orders, revenue, users, prescriptions and their statuses.",
)
def analytics_overview(db: Annotated[Session, Depends(get_db)]):
    """
    Top-level analytics KPIs for the admin dashboard header cards.

    Returns:
        dict: total_orders, total_revenue, total_users, total_medicines,
              pending_orders, fulfilled_orders, failed_orders,
              total_prescriptions, pending_prescriptions
    """
    return get_overview_stats(db)


@router.get(
    "/medicines",
    summary="Get top N medicines by order volume",
    description="Returns the most ordered medicines sorted by total quantity.",
)
def analytics_top_medicines(
    n: int = Query(default=10, ge=1, le=50, description="Number of top medicines"),
    db: Annotated[Session, Depends(get_db)],
):
    """
    Top medicines data for bar chart visualization.

    Args:
        n: How many top medicines to return (default 10, max 50)

    Returns:
        List of {medicine_id, medicine_name, total_quantity, total_orders, total_revenue}
    """
    return {"medicines": get_top_medicines(db, n=n)}


@router.get(
    "/refills",
    summary="Get refill alert statistics",
    description="Breakdown of refill alerts by status + top medicines with alerts.",
)
def analytics_refills(db: Annotated[Session, Depends(get_db)]):
    """
    Refill prediction stats for the analytics dashboard.

    Returns:
        dict: total, pending, notified, ordered, by_medicine (top 5)
    """
    return get_refill_stats(db)


@router.get(
    "/fulfillment",
    summary="Get webhook fulfillment statistics",
    description="Success rate, failure count, and recent webhook event history.",
)
def analytics_fulfillment(db: Annotated[Session, Depends(get_db)]):
    """
    Webhook/fulfillment analytics for admin monitoring.

    Returns:
        dict: total_attempts, successful, failed, success_rate, recent_events (last 20)
    """
    return get_webhook_stats(db)


@router.get(
    "/orders-over-time",
    summary="Daily order counts and revenue for line chart",
)
def analytics_orders_over_time(
    days: int = Query(default=30, ge=7, le=365, description="Days to look back"),
    db: Annotated[Session, Depends(get_db)],
):
    """
    Time-series order data for the analytics line chart.

    Args:
        days: Number of past days to include (default 30, range 7-365)

    Returns:
        List of {date, order_count, revenue}
    """
    return {"data": get_orders_over_time(db, days=days)}
