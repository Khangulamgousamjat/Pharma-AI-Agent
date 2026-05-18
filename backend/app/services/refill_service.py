"""
services/refill_service.py — Refill prediction business logic.

Phase 2 addition: Analyzes a user's order history and predicts
when they will run out of medicines, generating proactive alerts.

Prediction Algorithm:
  1. For each medicine the user has ordered in the last 90 days:
     a. Find their most recent order
     b. Assume daily consumption = quantity / standard_days_supply
        (e.g., 30 tablets → 1/day → 30 day supply)
     c. predicted_refill_date = last_order_date + days_supply
  2. If predicted_refill_date is within 7 days → create/update alert
  3. Status: 'pending' (default) → 'notified' (viewed) → 'ordered' (reordered)

Standard days supply assumptions (Phase 2):
  - Tablets / capsules: quantity ordered = days supply (1 per day assumed)
  - Bottles (syrups): 14 days per bottle
"""

import logging
from datetime import date, datetime, timedelta
from typing import List, Dict

from sqlalchemy.orm import Session

from app.models.order import Order
from app.models.refill_alert import RefillAlert
from app.schemas.refill import RefillPredictionResponse

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Prediction constants
# ---------------------------------------------------------------------------
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


def predict_refill_needs(db: Session, user_id: int) -> RefillPredictionResponse:
    """
    Predict refill dates from a user's recent order history.

    Analysis window: last 90 days of orders.
    Alert creation: only if predicted run-out is within ALERT_THRESHOLD_DAYS.

    Args:
        db: Database session
        user_id: User whose orders to analyze

    Returns:
        RefillPredictionResponse: Summary of alerts created/updated
    """
    logger.info(f"[RefillService] Running refill prediction for user={user_id}")

    # Fetch orders from last 90 days
    ninety_days_ago = datetime.utcnow() - timedelta(days=90)
    recent_orders: List[Order] = (
        db.query(Order)
        .filter(
            Order.user_id == user_id,
            Order.created_at >= ninety_days_ago,
            Order.status.in_(["confirmed", "paid"]),
        )
        .order_by(Order.created_at.desc())
        .all()
    )

    if not recent_orders:
        logger.info(f"[RefillService] No recent orders found for user={user_id}")
        return RefillPredictionResponse(
            user_id=user_id,
            alerts_created=0,
            alerts_updated=0,
            message="No recent orders found to analyze.",
        )

    # Group orders by medicine_id — keep only the most recent per medicine
    latest_by_medicine: Dict[int, Order] = {}
    for order in recent_orders:
        if order.medicine_id not in latest_by_medicine:
            latest_by_medicine[order.medicine_id] = order

    alerts_created = 0
    alerts_updated = 0
    today = date.today()

    for medicine_id, order in latest_by_medicine.items():
        # -----------------------------------------------------------------------
        # Calculate predicted refill date
        # -----------------------------------------------------------------------
        medicine = order.medicine
        if not medicine:
            continue

        # Determine days supply based on medicine unit type
        unit_lower = (medicine.unit or "tablets").lower()
        days_per_unit = DAYS_SUPPLY_PER_UNIT.get(unit_lower, DEFAULT_DAYS_PER_UNIT)
        days_supply = order.quantity * days_per_unit

        # Predicted refill date = order date + days supply
        if order.created_at:
            order_date = order.created_at.date() if hasattr(order.created_at, 'date') else order.created_at
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

        # -----------------------------------------------------------------------
        # Create or update the refill alert
        # -----------------------------------------------------------------------
        existing_alert = (
            db.query(RefillAlert)
            .filter(
                RefillAlert.user_id == user_id,
                RefillAlert.medicine_id == medicine_id,
                RefillAlert.status.in_(["pending", "notified"]),
            )
            .first()
        )

        if existing_alert:
            # Update existing alert with fresh prediction
            existing_alert.predicted_refill_date = predicted_refill_date
            existing_alert.days_supply = days_supply
            db.commit()
            alerts_updated += 1
            logger.info(f"[RefillService] Updated alert id={existing_alert.id}")
        else:
            # Create new alert
            alert = RefillAlert(
                user_id=user_id,
                medicine_id=medicine_id,
                predicted_refill_date=predicted_refill_date,
                days_supply=days_supply,
                status="pending",
            )
            db.add(alert)
            db.commit()
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


def get_user_refill_alerts(db: Session, user_id: int) -> List[RefillAlert]:
    """
    Get all active refill alerts for a user.

    Args:
        db: Database session
        user_id: User ID

    Returns:
        List[RefillAlert]: Alerts sorted by predicted refill date (soonest first)
    """
    return (
        db.query(RefillAlert)
        .filter(RefillAlert.user_id == user_id)
        .order_by(RefillAlert.predicted_refill_date.asc())
        .all()
    )


def get_all_refill_alerts(db: Session) -> List[RefillAlert]:
    """
    Get all refill alerts in the system (admin/pharmacist view).

    Returns:
        List[RefillAlert]: All alerts, soonest first
    """
    return (
        db.query(RefillAlert)
        .order_by(RefillAlert.predicted_refill_date.asc())
        .all()
    )


def mark_alert_notified(db: Session, alert_id: int) -> None:
    """
    Mark a refill alert as 'notified' (user has seen it in the UI).

    Args:
        db: Database session
        alert_id: Alert to update
    """
    alert = db.query(RefillAlert).filter(RefillAlert.id == alert_id).first()
    if alert and alert.status == "pending":
        alert.status = "notified"
        db.commit()


def mark_alert_ordered(db: Session, alert_id: int) -> None:
    """
    Mark a refill alert as 'ordered' (user clicked Reorder).

    Args:
        db: Database session
        alert_id: Alert to update
    """
    alert = db.query(RefillAlert).filter(RefillAlert.id == alert_id).first()
    if alert:
        alert.status = "ordered"
        db.commit()
