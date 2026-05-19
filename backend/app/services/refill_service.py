"""
services/refill_service.py — Refill prediction business logic using Firestore.
"""

import logging
from datetime import date, datetime, timedelta
from typing import List, Dict, Any

from fastapi import HTTPException, status

from app.models.order import Order
from app.models.refill_alert import RefillAlert
from app.models.medicine import Medicine
from app.schemas.refill import RefillPredictionResponse

logger = logging.getLogger(__name__)

# Days before predicted run-out date to generate a refill alert
ALERT_THRESHOLD_DAYS = 7

# Standard days supply per unit by medicine type
DAYS_SUPPLY_PER_UNIT = {
    "tablets": 1,   # 1 tablet = 1 day
    "capsules": 1,  # 1 capsule = 1 day
    "sachets": 1,   # 1 sachet = 1 day
    "bottles": 14,  # 1 bottle = 14 days
    "injections": 7,
}
DEFAULT_DAYS_PER_UNIT = 1


def _doc_to_alert(doc) -> RefillAlert:
    data = doc.to_dict()
    data['id'] = doc.id
    if 'created_at' in data and not isinstance(data['created_at'], str) and hasattr(data['created_at'], 'to_datetime'):
        data['created_at'] = data['created_at'].to_datetime()
    return RefillAlert(**data)


def _doc_to_order(doc) -> Order:
    data = doc.to_dict()
    data['id'] = doc.id
    if 'created_at' in data and not isinstance(data['created_at'], str) and hasattr(data['created_at'], 'to_datetime'):
        data['created_at'] = data['created_at'].to_datetime()
    return Order(**data)


def predict_refill_needs(db: Any, user_id: str) -> RefillPredictionResponse:
    """
    Predict refill dates from a user's recent order history in Firestore.
    """
    logger.info(f"[RefillService] Running refill prediction for user={user_id}")

    # Fetch orders
    ninety_days_ago = datetime.utcnow() - timedelta(days=90)
    docs = db.collection("orders").where("user_id", "==", user_id).stream()
    
    recent_orders: List[Order] = []
    for doc in docs:
        order = _doc_to_order(doc)
        if order.created_at >= ninety_days_ago and order.status in ["confirmed", "paid"]:
            recent_orders.append(order)

    if not recent_orders:
        logger.info(f"[RefillService] No recent orders found for user={user_id}")
        return RefillPredictionResponse(
            user_id=user_id,
            alerts_created=0,
            alerts_updated=0,
            message="No recent orders found to analyze.",
        )

    # Sort recent orders: newest first
    recent_orders.sort(key=lambda o: o.created_at, reverse=True)

    # Group orders by medicine_id — keep only the most recent per medicine
    latest_by_medicine: Dict[str, Order] = {}
    for order in recent_orders:
        if order.medicine_id not in latest_by_medicine:
            latest_by_medicine[order.medicine_id] = order

    alerts_created = 0
    alerts_updated = 0
    today = date.today()

    for medicine_id, order in latest_by_medicine.items():
        # Fetch medicine details
        med_doc = db.collection("medicines").document(medicine_id).get()
        if not med_doc.exists:
            continue
        
        med_data = med_doc.to_dict()
        med_data['id'] = med_doc.id
        medicine = Medicine(**med_data)

        # Determine days supply based on medicine unit type
        unit_lower = (medicine.unit or "tablets").lower()
        days_per_unit = DAYS_SUPPLY_PER_UNIT.get(unit_lower, DEFAULT_DAYS_PER_UNIT)
        days_supply = order.quantity * days_per_unit

        # Predicted refill date = order date + days supply
        if order.created_at:
            order_date = order.created_at.date() if hasattr(order.created_at, 'date') else order.created_at
            # Handle if order_date is a datetime
            if isinstance(order_date, datetime):
                order_date = order_date.date()
            predicted_refill_date = order_date + timedelta(days=days_supply)
        else:
            predicted_refill_date = today + timedelta(days=7)

        logger.info(
            f"[RefillService] medicine={medicine.name} qty={order.quantity} "
            f"days_supply={days_supply} predicted_refill={predicted_refill_date}"
        )

        # Only create alert if refill is due within threshold
        days_until_refill = (predicted_refill_date - today).days
        if days_until_refill > ALERT_THRESHOLD_DAYS:
            logger.info(
                f"[RefillService] {medicine.name}: {days_until_refill} days until refill, "
                f"skipping (threshold={ALERT_THRESHOLD_DAYS})"
            )
            continue

        # Check for existing pending or notified alerts
        alerts_query = db.collection("refill_alerts")\
                        .where("user_id", "==", user_id)\
                        .where("medicine_id", "==", medicine_id)\
                        .stream()
                        
        existing_alert_doc = None
        for alert_doc in alerts_query:
            a_data = alert_doc.to_dict()
            if a_data.get("status") in ["pending", "notified"]:
                existing_alert_doc = alert_doc
                break

        pred_date_str = predicted_refill_date.isoformat()

        if existing_alert_doc:
            # Update existing alert with fresh prediction
            db.collection("refill_alerts").document(existing_alert_doc.id).update({
                "predicted_refill_date": pred_date_str,
                "days_supply": days_supply
            })
            alerts_updated += 1
            logger.info(f"[RefillService] Updated alert id={existing_alert_doc.id}")
        else:
            # Create new alert
            new_ref = db.collection("refill_alerts").document()
            alert = RefillAlert(
                id=new_ref.id,
                user_id=user_id,
                medicine_id=medicine_id,
                predicted_refill_date=pred_date_str,
                days_supply=days_supply,
                status="pending",
            )
            new_ref.set(alert.to_dict())
            alerts_created += 1
            logger.info(f"[RefillService] Created new refill alert for medicine={medicine.name}")

    return RefillPredictionResponse(
        user_id=user_id,
        alerts_created=alerts_created,
        alerts_updated=alerts_updated,
        message=(
            f"Prediction complete. {alerts_created} new alert(s) created, "
            f"{alerts_updated} alert(s) updated."
        ),
    )


def get_user_refill_alerts(db: Any, user_id: str) -> List[RefillAlert]:
    """
    Get all active refill alerts for a user from Firestore.
    """
    docs = db.collection("refill_alerts").where("user_id", "==", user_id).stream()
    alerts = [_doc_to_alert(doc) for doc in docs]
    alerts.sort(key=lambda a: a.predicted_refill_date or "")
    return alerts


def get_all_refill_alerts(db: Any) -> List[RefillAlert]:
    """
    Get all refill alerts in the system (admin/pharmacist view) from Firestore.
    """
    docs = db.collection("refill_alerts").stream()
    alerts = [_doc_to_alert(doc) for doc in docs]
    alerts.sort(key=lambda a: a.predicted_refill_date or "")
    return alerts


def mark_alert_notified(db: Any, alert_id: str) -> None:
    """
    Mark a refill alert as 'notified' in Firestore.
    """
    doc_ref = db.collection("refill_alerts").document(alert_id)
    doc = doc_ref.get()
    if doc.exists and doc.to_dict().get("status") == "pending":
        doc_ref.update({"status": "notified"})


def mark_alert_ordered(db: Any, alert_id: str) -> None:
    """
    Mark a refill alert as 'ordered' in Firestore.
    """
    doc_ref = db.collection("refill_alerts").document(alert_id)
    if doc_ref.get().exists:
        doc_ref.update({"status": "ordered"})
