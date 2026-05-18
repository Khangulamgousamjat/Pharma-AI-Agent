import logging
from langsmith import traceable

from app.agents.pharmacy_agent import get_pharmacy_agent
from app.agents.stock_agent import StockAgent
from app.agents.prescription_agent import PrescriptionAgent
from app.agents.payment_agent import PaymentAgent
from app.agents.order_agent import OrderAgent
from app.agents.delivery_agent import DeliveryAgent
from app.agents.notification_agent import NotificationAgent

logger = logging.getLogger(__name__)

class AgentCoordinator:
    """
    AgentCoordinator
    Orchestrates specialized sub-agents in a chronological sequence:
    Conversation -> Stock -> Prescription -> Payment -> Order -> Delivery -> Notification.
    """
    def __init__(self):
        self.stock_agent = StockAgent()
        self.prescription_agent = PrescriptionAgent()
        self.payment_agent = PaymentAgent()
        self.order_agent = OrderAgent()
        self.delivery_agent = DeliveryAgent()
        self.notification_agent = NotificationAgent()

    @traceable(name="AgentCoordinator.execute_fulfillment_sequence")
    def execute_fulfillment_sequence(self, user_id: int, medicine_id: int, qty: int, price: float, user_email: str, address: str):
        """Processes the master chain of agents to fulfill an end-to-end request."""
        logger.info(f"AgentCoordinator: Commencing sequence for {qty}x med_{medicine_id}")
        
        # 1. Check Stock
        if not self.stock_agent.check_availability(medicine_id, qty):
            return {"status": "failed", "reason": "out_of_stock"}
            
        # 2. Check Prescription Rules
        if not self.prescription_agent.validate_rx(user_id, medicine_id):
            return {"status": "failed", "reason": "rx_required"}
            
        # 3. Simulate Payment
        charge = self.payment_agent.initiate_charge(user_id, price * qty)
        
        # 4. Draft Order Formalities
        draft = self.order_agent.draft_order(user_id, medicine_id, qty)
        
        # 5. Schedule Logistics
        delivery = self.delivery_agent.schedule_delivery(draft["draft_id"], address)
        
        # 6. Notify Endpoint User
        if user_email:
            self.notification_agent.send_order_confirmation(user_email, draft["draft_id"], price * qty)
            
        logger.info("AgentCoordinator: Sequence completed successfully.")
        return {
            "status": "success",
            "order_id": draft["draft_id"],
            "delivery": delivery["status"]
        }
