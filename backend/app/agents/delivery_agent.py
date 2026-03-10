import logging
from langsmith import traceable

logger = logging.getLogger(__name__)

class DeliveryAgent:
    """
    DeliveryAgent
    Responsible for scheduling and tracking multi-leg logistics endpoints.
    """
    @traceable(name="DeliveryAgent.schedule_delivery")
    def schedule_delivery(self, order_id: int, address: str) -> dict:
        """Creates formal dispatch with courier aggregation."""
        logger.info(f"Scheduling dispatch for order {order_id} to {address}")
        return {"status": "en_route", "tracking": f"TRK-{order_id}"}
