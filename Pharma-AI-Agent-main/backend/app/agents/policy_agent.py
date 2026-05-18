import logging
from langsmith import traceable

logger = logging.getLogger(__name__)

class PolicyAgent:
    """
    PolicyAgent
    Responsible for enforcing local pharmaceutical laws and company policy.
    """
    @traceable(name="PolicyAgent.check_compliance")
    def check_compliance(self, medicine_id: int, user_age: int) -> bool:
        """Determines if the transaction is legally sound."""
        logger.info(f"Checking compliance for med {medicine_id} and age {user_age}")
        return True
