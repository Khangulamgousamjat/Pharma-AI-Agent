"""
services/analytics_service.py — Admin analytics and KPI computation using Firestore.
"""

import logging
from datetime import datetime, timedelta, date
from typing import List, Dict, Any

from app.models.order import Order
from app.models.medicine import Medicine
from app.models.user import User
from app.models.refill_alert import RefillAlert
from app.models.webhook_event import WebhookEvent
from app.models.prescription import Prescription

logger = logging.getLogger(__name__)


def _parse_created_at(data: dict) -> datetime:
    val = data.get("created_at")
    if not val:
        return datetime.utcnow()
    if isinstance(val, datetime):
        return val
    if not isinstance(val, str) and hasattr(val, 'to_datetime'):
        return val.to_datetime()
    try:
        return datetime.fromisoformat(val.replace("Z", "+00:00"))
    except Exception:
        return datetime.utcnow()


def get_overview_stats(db: Any) -> Dict[str, Any]:
    """
    Compute top-level KPI metrics for the analytics dashboard using Firestore.
    """
    orders_stream = db.collection("orders").stream()
    total_orders = 0
    total_revenue = 0.0
    pending_orders = 0
    fulfilled_orders = 0
    failed_orders = 0

    for doc in orders_stream:
        data = doc.to_dict()
        total_orders += 1
        total_revenue += float(data.get("total_price") or 0.0)
        status = data.get("status")
        if status == "pending":
            pending_orders += 1
        elif status == "fulfilled":
            fulfilled_orders += 1
        elif status == "fulfillment_failed":
            failed_orders += 1

    users_count = len(list(db.collection("users").list_documents()))
    medicines_count = len(list(db.collection("medicines").list_documents()))

    prescriptions_stream = db.collection("prescriptions").stream()
    total_prescriptions = 0
    pending_prescriptions = 0
    for doc in prescriptions_stream:
        data = doc.to_dict()
        total_prescriptions += 1
        if not data.get("verified", False):
            pending_prescriptions += 1

    return {
        "total_orders": total_orders,
        "total_revenue": round(total_revenue, 2),
        "total_users": users_count,
        "total_medicines": medicines_count,
        "pending_orders": pending_orders,
        "fulfilled_orders": fulfilled_orders,
        "failed_orders": failed_orders,
        "total_prescriptions": total_prescriptions,
        "pending_prescriptions": pending_prescriptions,
    }


def get_top_medicines(db: Any, n: int = 10) -> List[Dict[str, Any]]:
    """
    Get the top N most ordered medicines by total quantity from Firestore.
    """
    # Fetch medicine names
    med_docs = db.collection("medicines").stream()
    med_names = {doc.id: doc.to_dict().get("name", "Unknown Medicine") for doc in med_docs}

    orders_stream = db.collection("orders").stream()
    aggregates = {}

    for doc in orders_stream:
        data = doc.to_dict()
        med_id = data.get("medicine_id")
        if not med_id:
            continue
        qty = int(data.get("quantity") or 0)
        rev = float(data.get("total_price") or 0.0)

        if med_id not in aggregates:
            aggregates[med_id] = {
                "medicine_id": med_id,
                "medicine_name": med_names.get(med_id, f"Medicine#{med_id}"),
                "total_quantity": 0,
                "total_orders": 0,
                "total_revenue": 0.0,
            }
        
        aggregates[med_id]["total_quantity"] += qty
        aggregates[med_id]["total_orders"] += 1
        aggregates[med_id]["total_revenue"] += rev

    results = list(aggregates.values())
    results.sort(key=lambda x: x["total_quantity"], reverse=True)
    
    # Round revenue
    for r in results:
        r["total_revenue"] = round(r["total_revenue"], 2)

    return results[:n]


def get_refill_stats(db: Any) -> Dict[str, Any]:
    """
    Get refill alert statistics broken down by status from Firestore.
    """
    alerts_stream = db.collection("refill_alerts").stream()
    total = 0
    pending = 0
    notified = 0
    ordered = 0
    med_counts = {}

    # Fetch medicine names
    med_docs = db.collection("medicines").stream()
    med_names = {doc.id: doc.to_dict().get("name", "Unknown Medicine") for doc in med_docs}

    for doc in alerts_stream:
        data = doc.to_dict()
        total += 1
        status = data.get("status")
        if status == "pending":
            pending += 1
        elif status == "notified":
            notified += 1
        elif status == "ordered":
            ordered += 1
        
        med_id = data.get("medicine_id")
        if med_id:
            med_counts[med_id] = med_counts.get(med_id, 0) + 1

    by_medicine = []
    for med_id, count in med_counts.items():
        by_medicine.append({
            "medicine_name": med_names.get(med_id, f"Medicine#{med_id}"),
            "count": count
        })
    
    by_medicine.sort(key=lambda x: x["count"], reverse=True)

    return {
        "total": total,
        "pending": pending,
        "notified": notified,
        "ordered": ordered,
        "by_medicine": by_medicine[:5],
    }


def get_webhook_stats(db: Any) -> Dict[str, Any]:
    """
    Get fulfillment webhook success and failure statistics from Firestore.
    """
    events_stream = db.collection("webhook_events").stream()
    total = 0
    successful = 0
    failed = 0
    all_events = []

    for doc in events_stream:
        data = doc.to_dict()
        total += 1
        status = data.get("status")
        if status == "success":
            successful += 1
        elif status == "failed":
            failed += 1
        
        created_at = _parse_created_at(data)
        all_events.append({
            "id": doc.id,
            "order_id": data.get("order_id"),
            "attempt_number": data.get("attempt_number"),
            "status": status,
            "http_status_code": data.get("http_status_code"),
            "created_at": created_at,
        })

    success_rate = round((successful / total * 100) if total > 0 else 0.0, 1)

    all_events.sort(key=lambda e: e["created_at"], reverse=True)
    recent = all_events[:20]
    
    # Format created_at to ISO string for response
    for e in recent:
        e["created_at"] = e["created_at"].isoformat()

    return {
        "total_attempts": total,
        "successful": successful,
        "failed": failed,
        "success_rate": success_rate,
        "recent_events": recent,
    }


def get_orders_over_time(db: Any, days: int = 30) -> List[Dict[str, Any]]:
    """
    Get daily order counts for the last N days from Firestore.
    """
    cutoff = datetime.utcnow() - timedelta(days=days)
    orders_stream = db.collection("orders").stream()
    daily_stats = {}

    for doc in orders_stream:
        data = doc.to_dict()
        created_at = _parse_created_at(data)
        if created_at < cutoff:
            continue
        
        day_str = created_at.date().isoformat()
        rev = float(data.get("total_price") or 0.0)

        if day_str not in daily_stats:
            daily_stats[day_str] = {
                "date": day_str,
                "order_count": 0,
                "revenue": 0.0
            }
        
        daily_stats[day_str]["order_count"] += 1
        daily_stats[day_str]["revenue"] += rev

    results = list(daily_stats.values())
    results.sort(key=lambda x: x["date"])

    for r in results:
        r["revenue"] = round(r["revenue"], 2)

    return results
