"""
routes/refill_alerts.py — Refill alert and prediction API using Firestore.
"""

import logging
from typing import List, Any

from fastapi import APIRouter, Depends, status

from app.firebase_db import get_db
from app.schemas.refill import RefillAlertResponse, RefillPredictionRequest, RefillPredictionResponse
from app.services.refill_service import get_user_refill_alerts, get_all_refill_alerts
from app.services.medicine_service import get_all_medicines
from app.agents.refill_agent import get_refill_agent

router = APIRouter(prefix="/refill-alerts", tags=["Refill Alerts"])
logger = logging.getLogger(__name__)


@router.get(
    "/user/{user_id}",
    response_model=List[RefillAlertResponse],
    summary="Get refill alerts for a specific user",
)
def get_user_alerts(
    user_id: str,
    db: Any = Depends(get_db),
):
    alerts = get_user_refill_alerts(db, user_id)
    
    # Pre-load medicine mappings to avoid N+1 queries
    meds = get_all_medicines(db)
    med_map = {m.id: m for m in meds}

    result = []
    for a in alerts:
        med = med_map.get(a.medicine_id)
        result.append(RefillAlertResponse(
            id=a.id,
            user_id=a.user_id,
            medicine_id=a.medicine_id,
            predicted_refill_date=a.predicted_refill_date,
            days_supply=a.days_supply,
            status=a.status,
            created_at=a.created_at,
            medicine_name=med.name if med else None,
            medicine_unit=med.unit if med else None,
        ))
    return result


@router.get(
    "/all",
    response_model=List[RefillAlertResponse],
    summary="Get all refill alerts (admin/pharmacist view)",
)
def get_all_alerts(
    db: Any = Depends(get_db),
):
    alerts = get_all_refill_alerts(db)
    
    meds = get_all_medicines(db)
    med_map = {m.id: m for m in meds}

    result = []
    for a in alerts:
        med = med_map.get(a.medicine_id)
        result.append(RefillAlertResponse(
            id=a.id,
            user_id=a.user_id,
            medicine_id=a.medicine_id,
            predicted_refill_date=a.predicted_refill_date,
            days_supply=a.days_supply,
            status=a.status,
            created_at=a.created_at,
            medicine_name=med.name if med else None,
            medicine_unit=med.unit if med else None,
        ))
    return result


@router.post(
    "/run-prediction",
    response_model=RefillPredictionResponse,
    status_code=status.HTTP_200_OK,
    summary="Trigger refill prediction for a user",
)
async def run_prediction(
    request: RefillPredictionRequest,
    db: Any = Depends(get_db),
):
    logger.info(f"[RefillRoute] Running prediction for user_id={request.user_id}")
    refill_agent = get_refill_agent()
    result = await refill_agent.predict(db, request.user_id)
    return result
