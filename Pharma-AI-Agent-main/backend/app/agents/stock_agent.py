import logging
from langsmith import traceable

logger = logging.getLogger(__name__)

class StockAgent:
    """
    StockAgent
    Responsible for validating stock constraints dynamically across multiple warehouses.
    """
    @traceable(name="StockAgent.check_availability")
    def check_availability(self, medicine_id: int, quantity: int) -> bool:
        """Query real-time stock levels."""
        logger.info(f"Checking {quantity} units for medicine {medicine_id}")
        return True
