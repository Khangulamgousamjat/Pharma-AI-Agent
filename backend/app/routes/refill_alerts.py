"""
routes/refill_alerts.py — Refill alert and prediction API.

Phase 2 addition: Endpoints to view refill predictions and trigger the
Refill Prediction Agent.

Endpoints:
  GET  /refill-alerts/user/{user_id}   — User's refill alerts
  GET  /refill-alerts/all              — All alerts (admin)
  POST /refill-alerts/run-prediction   — Trigger prediction for a user
"""

import logging
from typing import List

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.refill import RefillAlertResponse, RefillPredictionRequest, RefillPredictionResponse
from app.services.refill_service import get_user_refill_alerts, get_all_refill_alerts
from app.agents.refill_agent import get_refill_agent

router = APIRouter(prefix="/refill-alerts", tags=["Refill Alerts"])
logger = logging.getLogger(__name__)


@router.get(
    "/user/{user_id}",
    response_model=List[RefillAlertResponse],
    summary="Get refill alerts for a specific user",
    description="Returns AI-predicted refill dates for medicines the user has ordered.",
)
def get_user_alerts(
    user_id: int,
    db: Session = Depends(get_db),
):
    """
    Get all active refill alerts for a user.

    Alerts are ordered by predicted refill date (soonest first).
    Each alert contains: medicine name, predicted date, days supply, status.
    """
    alerts = get_user_refill_alerts(db, user_id)
    result = []
    for a in alerts:
        result.append(RefillAlertResponse(
            id=a.id,
            user_id=a.user_id,
            medicine_id=a.medicine_id,
            predicted_refill_date=a.predicted_refill_date,
            days_supply=a.days_supply,
            status=a.status,
            created_at=a.created_at,
            medicine_name=a.medicine.name if a.medicine else None,
            medicine_unit=a.medicine.unit if a.medicine else None,
        ))
    return result


@router.get(
    "/all",
    response_model=List[RefillAlertResponse],
    summary="Get all refill alerts (admin/pharmacist view)",
)
def get_all_alerts(
    db: Session = Depends(get_db),
):
    """
    Get all refill alerts across all users — for admin monitoring.
    """
    alerts = get_all_refill_alerts(db)
    result = []
    for a in alerts:
        result.append(RefillAlertResponse(
            id=a.id,
            user_id=a.user_id,
            medicine_id=a.medicine_id,
            predicted_refill_date=a.predicted_refill_date,
            days_supply=a.days_supply,
            status=a.status,
            created_at=a.created_at,
            medicine_name=a.medicine.name if a.medicine else None,
            medicine_unit=a.medicine.unit if a.medicine else None,
        ))
    return result


@router.post(
    "/run-prediction",
    response_model=RefillPredictionResponse,
    status_code=status.HTTP_200_OK,
    summary="Trigger refill prediction for a user",
    description="Runs the Refill Agent to analyze order history and create/update alerts.",
)
async def run_prediction(
    request: RefillPredictionRequest,
    db: Session = Depends(get_db),
):
    """
    Trigger the Refill Prediction Agent for a specific user.

    Analyzes the user's last 90 days of orders, calculates days supply
    remaining for each medicine, and creates refill alerts for medicines
    due within 7 days.

    This endpoint can be called:
    - Manually by admin/pharmacist from the dashboard
    - After an order is created (for proactive alerts)
    """
    logger.info(f"[RefillRoute] Running prediction for user_id={request.user_id}")
    refill_agent = get_refill_agent()
    result = await refill_agent.predict(db, request.user_id)
    return result
