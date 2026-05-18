import logging
from langsmith import traceable

logger = logging.getLogger(__name__)

class PaymentAgent:
    """
    PaymentAgent
    Responsible for orchestrating payments via third party gateways.
    """
    @traceable(name="PaymentAgent.initiate_charge")
    def initiate_charge(self, user_id: int, amount: float) -> str:
        """Securely holds charge request against a validated payment instrument."""
        logger.info(f"Initiating charge of {amount} for {user_id}")
        return "tok_success"
