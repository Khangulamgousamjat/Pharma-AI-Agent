import logging
from langsmith import traceable

logger = logging.getLogger(__name__)

class OrderAgent:
    """
    OrderAgent
    Responsible for formalizing transaction blocks into DB models.
    """
    @traceable(name="OrderAgent.draft_order")
    def draft_order(self, user_id: int, medicine_id: int, qty: int) -> dict:
        """Mints the payload parameters for order processing."""
        logger.info(f"Drafting order of {qty} med {medicine_id} for user {user_id}")
        return {"draft_id": 1234, "status": "pending_creation"}
