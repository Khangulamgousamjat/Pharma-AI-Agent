"""
services/analytics_service.py — Admin analytics and KPI computation.

Phase 3 addition: Computes aggregated metrics for the Admin Analytics
dashboard. All queries are read-only and operate on existing tables.

Functions:
  get_overview_stats   — high-level KPIs
  get_top_medicines    — most ordered medicines
  get_refill_stats     — refill alert counts by status
  get_webhook_stats    — fulfillment success rates

Performance note:
  These queries run against the live DB. For very large datasets,
  add caching (Redis / functools.lru_cache with TTL) in Phase 4.
"""

import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any

from sqlalchemy import func, desc
from sqlalchemy.orm import Session

from app.models.order import Order
from app.models.medicine import Medicine
from app.models.user import User
from app.models.refill_alert import RefillAlert
from app.models.webhook_event import WebhookEvent

logger = logging.getLogger(__name__)


def get_overview_stats(db: Session) -> Dict[str, Any]:
    """
    Compute top-level KPI metrics for the analytics dashboard.

    Returns:
        dict: {
            total_orders, total_revenue, total_users, total_medicines,
            pending_orders, fulfilled_orders, failed_orders,
            total_prescriptions, pending_prescriptions
        }
    """
    from app.models.prescription import Prescription

    total_orders = db.query(func.count(Order.id)).scalar() or 0
    total_revenue = db.query(func.sum(Order.total_price)).scalar() or 0.0
    total_users = db.query(func.count(User.id)).scalar() or 0
    total_medicines = db.query(func.count(Medicine.id)).scalar() or 0

    pending_orders = db.query(func.count(Order.id)).filter(Order.status == "pending").scalar() or 0
    fulfilled_orders = db.query(func.count(Order.id)).filter(Order.status == "fulfilled").scalar() or 0
    failed_orders = db.query(func.count(Order.id)).filter(Order.status == "fulfillment_failed").scalar() or 0

    total_prescriptions = db.query(func.count(Prescription.id)).scalar() or 0
    pending_prescriptions = (
        db.query(func.count(Prescription.id))
        .filter(Prescription.verified == False)  # noqa
        .scalar() or 0
    )

    return {
        "total_orders": total_orders,
        "total_revenue": round(float(total_revenue), 2),
        "total_users": total_users,
        "total_medicines": total_medicines,
        "pending_orders": pending_orders,
        "fulfilled_orders": fulfilled_orders,
        "failed_orders": failed_orders,
        "total_prescriptions": total_prescriptions,
        "pending_prescriptions": pending_prescriptions,
    }


def get_top_medicines(db: Session, n: int = 10) -> List[Dict[str, Any]]:
    """
    Get the top N most ordered medicines by total quantity.

    Args:
        db: Database session
        n: Number of top medicines to return (default 10)

    Returns:
        List of dicts: [{medicine_id, medicine_name, total_quantity, total_orders, total_revenue}]
    """
    results = (
        db.query(
            Order.medicine_id,
            Medicine.name.label("medicine_name"),
            func.sum(Order.quantity).label("total_quantity"),
            func.count(Order.id).label("total_orders"),
            func.sum(Order.total_price).label("total_revenue"),
        )
        .join(Medicine, Order.medicine_id == Medicine.id)
        .group_by(Order.medicine_id, Medicine.name)
        .order_by(desc("total_quantity"))
        .limit(n)
        .all()
    )

    return [
        {
            "medicine_id": r.medicine_id,
            "medicine_name": r.medicine_name,
            "total_quantity": int(r.total_quantity or 0),
            "total_orders": int(r.total_orders or 0),
            "total_revenue": round(float(r.total_revenue or 0), 2),
        }
        for r in results
    ]


def get_refill_stats(db: Session) -> Dict[str, Any]:
    """
    Get refill alert statistics broken down by status.

    Returns:
        dict: {
            total, pending, notified, ordered,
            by_medicine: [{medicine_name, count}]
        }
    """
    total = db.query(func.count(RefillAlert.id)).scalar() or 0
    pending = db.query(func.count(RefillAlert.id)).filter(RefillAlert.status == "pending").scalar() or 0
    notified = db.query(func.count(RefillAlert.id)).filter(RefillAlert.status == "notified").scalar() or 0
    ordered = db.query(func.count(RefillAlert.id)).filter(RefillAlert.status == "ordered").scalar() or 0

    # Top medicines with refill alerts
    by_medicine_rows = (
        db.query(
            Medicine.name.label("medicine_name"),
            func.count(RefillAlert.id).label("count"),
        )
        .join(Medicine, RefillAlert.medicine_id == Medicine.id)
        .group_by(Medicine.name)
        .order_by(desc("count"))
        .limit(5)
        .all()
    )

    return {
        "total": total,
        "pending": pending,
        "notified": notified,
        "ordered": ordered,
        "by_medicine": [
            {"medicine_name": r.medicine_name, "count": int(r.count)}
            for r in by_medicine_rows
        ],
    }


def get_webhook_stats(db: Session) -> Dict[str, Any]:
    """
    Get fulfillment webhook success and failure statistics.

    Returns:
        dict: {
            total_attempts, successful, failed, success_rate,
            recent_events: [{order_id, status, attempt_number, created_at}]
        }
    """
    total = db.query(func.count(WebhookEvent.id)).scalar() or 0
    successful = (
        db.query(func.count(WebhookEvent.id))
        .filter(WebhookEvent.status == "success")
        .scalar() or 0
    )
    failed = (
        db.query(func.count(WebhookEvent.id))
        .filter(WebhookEvent.status == "failed")
        .scalar() or 0
    )

    success_rate = round((successful / total * 100) if total > 0 else 0.0, 1)

    # Last 20 events
    recent = (
        db.query(WebhookEvent)
        .order_by(WebhookEvent.created_at.desc())
        .limit(20)
        .all()
    )

    return {
        "total_attempts": total,
        "successful": successful,
        "failed": failed,
        "success_rate": success_rate,
        "recent_events": [
            {
                "id": e.id,
                "order_id": e.order_id,
                "attempt_number": e.attempt_number,
                "status": e.status,
                "http_status_code": e.http_status_code,
                "created_at": e.created_at.isoformat() if e.created_at else None,
            }
            for e in recent
        ],
    }


def get_orders_over_time(db: Session, days: int = 30) -> List[Dict[str, Any]]:
    """
    Get daily order counts for the last N days (for line chart).

    Args:
        db: Database session
        days: Number of days to look back

    Returns:
        List of dicts: [{date, order_count, revenue}]
    """
    cutoff = datetime.utcnow() - timedelta(days=days)

    results = (
        db.query(
            func.date(Order.created_at).label("date"),
            func.count(Order.id).label("order_count"),
            func.sum(Order.total_price).label("revenue"),
        )
        .filter(Order.created_at >= cutoff)
        .group_by(func.date(Order.created_at))
        .order_by("date")
        .all()
    )

    return [
        {
            "date": str(r.date),
            "order_count": int(r.order_count or 0),
            "revenue": round(float(r.revenue or 0), 2),
        }
        for r in results
    ]
