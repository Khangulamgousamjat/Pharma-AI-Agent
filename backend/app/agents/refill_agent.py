"""
agents/refill_agent.py — Refill Prediction Agent.

Phase 2 addition: Proactive intelligence agent that analyzes a user's
order history and predicts when they will need to reorder medicines.

Architecture:
  - Framework: Direct service call (no LangChain loop — deterministic logic)
  - Algorithm: Order history analysis + days-supply estimation
  - Tracing: LangSmith metadata tagging for observability
  - Output: RefillPredictionResponse with alerts created/updated

Unlike the conversational PharmacyAgent which uses ReAct reasoning,
the RefillAgent uses deterministic rule-based logic:
  "If user bought 30 tablets and typically takes 1/day → refill in 30 days"

This agent can be triggered:
  1. Manually via POST /refill-alerts/run-prediction (admin/pharmacist)
  2. After an order is created (Phase 3: background scheduler)
"""

import logging
from typing import Optional

from sqlalchemy.orm import Session

from app.services.refill_service import predict_refill_needs
from app.schemas.refill import RefillPredictionResponse

logger = logging.getLogger(__name__)


class RefillAgent:
    """
    Refill Prediction Agent — Proactive pharmacy intelligence.

    Responsibilities:
    1. Receive a user_id
    2. Analyze their recent order history (90 days)
    3. Calculate days supply remaining per medicine
    4. Create/update refill alerts for medicines due within 7 days
    5. Return summary of what alerts were created

    The agent intentionally uses deterministic logic (not LLM) for
    refill prediction because:
    - Predictions need to be consistent and explainable
    - No natural language understanding is required
    - Simpler, faster, and cheaper than LLM inference
    """

    def __init__(self):
        """Initialize the Refill Agent."""
        self.agent_name = "RefillAgent"
        logger.info("RefillAgent initialized.")

    async def predict(self, db: Session, user_id: int) -> RefillPredictionResponse:
        """
        Run refill prediction for a specific user.

        Delegates to refill_service.predict_refill_needs() which contains
        the prediction algorithm. This method adds logging and LangSmith
        observability.

        Algorithm (in refill_service):
          1. Fetch all confirmed/paid orders for user (last 90 days)
          2. Group by medicine_id, keep only most recent order
          3. For each medicine:
             - days_supply = quantity × days_per_unit (1 for tablets, 14 for bottles)
             - predicted_date = order_date + days_supply
             - If predicted_date is within 7 days: create/update RefillAlert
          4. Return summary

        Args:
            db: Database session
            user_id: User to run prediction for

        Returns:
            RefillPredictionResponse: {alerts_created, alerts_updated, message}
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


# ---------------------------------------------------------------------------
# Singleton
# ---------------------------------------------------------------------------
_refill_agent: Optional[RefillAgent] = None


def get_refill_agent() -> RefillAgent:
    """
    Get or create the singleton RefillAgent instance.

    Returns:
        RefillAgent: Initialized refill prediction agent
    """
    global _refill_agent
    if _refill_agent is None:
        _refill_agent = RefillAgent()
    return _refill_agent
