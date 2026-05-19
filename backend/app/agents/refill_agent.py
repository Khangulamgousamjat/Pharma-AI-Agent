"""
agents/refill_agent.py — Refill Prediction Agent using Firestore.
"""

import logging
from typing import Optional, Any

from app.services.refill_service import predict_refill_needs
from app.schemas.refill import RefillPredictionResponse

logger = logging.getLogger(__name__)


class RefillAgent:
    """
    Refill Prediction Agent — Proactive pharmacy intelligence.
    """

    def __init__(self):
        self.agent_name = "RefillAgent"
        logger.info("RefillAgent initialized.")

    async def predict(self, db: Any, user_id: str) -> RefillPredictionResponse:
        """
        Run refill prediction for a specific user using Firestore.
        """
        logger.info(f"[RefillAgent] Running prediction for user={user_id}")

        try:
            result = predict_refill_needs(db, user_id)

            logger.info(
                f"[RefillAgent] Prediction complete: "
                f"created={result.alerts_created} updated={result.alerts_updated}"
            )
            return result

        except Exception as e:
            logger.error(f"[RefillAgent] Prediction failed for user={user_id}: {e}", exc_info=True)
            return RefillPredictionResponse(
                user_id=user_id,
                alerts_created=0,
                alerts_updated=0,
                message=f"Prediction failed: {str(e)}",
            )


_refill_agent: Optional[RefillAgent] = None


def get_refill_agent() -> RefillAgent:
    global _refill_agent
    if _refill_agent is None:
        _refill_agent = RefillAgent()
    return _refill_agent
