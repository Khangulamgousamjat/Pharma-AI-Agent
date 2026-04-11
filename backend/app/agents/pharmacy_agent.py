"""
agents/pharmacy_agent.py — Core LangGraph ReAct Agent for PharmaAgent AI.

Architecture:
    - LLM: Google Gemini 2.0 Flash via langchain_google_genai
    - Framework: LangGraph prebuilt create_react_agent
    - Tools: check_medicine_availability, create_pharmacy_order, get_order_history
    - Observability: LangSmith tracing
"""

import os
import logging
from typing import Optional

from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.prebuilt import create_react_agent
from langchain_core.messages import SystemMessage, HumanMessage

from app.config import settings
from app.agents.tools import PHARMACY_TOOLS, set_db_session

logger = logging.getLogger(__name__)

os.environ["LANGCHAIN_TRACING_V2"] = settings.langchain_tracing_v2
os.environ["LANGCHAIN_API_KEY"] = settings.langchain_api_key
os.environ["LANGCHAIN_PROJECT"] = settings.langchain_project


PHARMACY_SYSTEM_TEMPLATE = """You are PharmaBot, an intelligent and helpful AI pharmacist assistant for PharmaAgent AI pharmacy.

Your responsibilities:
1. Help users find medicines and check their availability
2. Process medicine orders for users (OTC medicines only, automatically)
3. Reject prescription medicines with a clear explanation
4. Provide helpful information about medicines

CRITICAL SAFETY RULES:
- ALWAYS call check_medicine_availability FIRST before attempting to order
- If prescription_required is true, NEVER create the order - explain the prescription requirement
- If out of stock, suggest alternatives or advise the user
- Be friendly, professional, and empathetic

User ID for this session: {user_id}
"""


class PharmacyAgent:
    """
    PharmaAgent AI — LangGraph-powered pharmacy assistant.
    """

    def __init__(self):
        logger.info("Initializing PharmacyAgent with Gemini 2.0 Flash...")
        
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-2.0-flash",
            google_api_key=settings.gemini_api_key,
            temperature=0.1,
            convert_system_message_to_human=True,
        )

        self.executor = create_react_agent(
            self.llm,
            tools=PHARMACY_TOOLS,
        )

        logger.info("PharmacyAgent initialized successfully.")

    async def chat(
        self,
        user_id: int,
        message: str,
        db,
    ) -> dict:
        """
        Process a user message through the pharmacy agent.
        """
        set_db_session(db)

        logger.info(f"Agent processing message from user={user_id}: '{message[:80]}...' ")

        try:
            system_msg = SystemMessage(content=PHARMACY_SYSTEM_TEMPLATE.format(user_id=user_id))
            user_msg = HumanMessage(content=message)

            result = await self.executor.ainvoke({
                "messages": [system_msg, user_msg]
            })

            messages = result.get("messages", [])
            raw_content = messages[-1].content if messages else "I'm sorry, I couldn't process your request."
            # LangChain AIMessage.content can be str or list (multimodal); ensure we always return str
            if isinstance(raw_content, list):
                parts = [
                    c.get("text", "") if isinstance(c, dict) else str(c)
                    for c in raw_content
                ]
                final_message = " ".join(parts).strip() or "I'm sorry, I couldn't process your request."
            else:
                final_message = str(raw_content) if raw_content else "I'm sorry, I couldn't process your request."
            
            # Analyze tool calls to find the action
            action = "info"
            order_id = None
            
            for msg in messages:
                if msg.type == "ai" and getattr(msg, "tool_calls", None):
                    for tc in msg.tool_calls:
                        if tc["name"] == "create_pharmacy_order":
                            action = "order_created"
                            # Order ID needs extraction from tool output, but simplify for now
                            # by parsing the final message or looking at next tool message
            
            # Look at ToolMessages to find the order_id if order_created
            for msg in messages:
                if msg.type == "tool" and msg.name == "create_pharmacy_order":
                    import json
                    try:
                        obs = json.loads(msg.content)
                        if obs.get("success"):
                            action = "order_created"
                            order_id = obs.get("order_id")
                        elif obs.get("action") == "prescription_required":
                            action = "prescription_required"
                        elif obs.get("action") == "out_of_stock":
                            action = "out_of_stock"
                        else:
                            action = "error"
                    except Exception:
                        pass
                
                # If they called check_availability and it returned prescription_required
                if msg.type == "tool" and msg.name == "check_medicine_availability":
                    try:
                        obs = json.loads(msg.content)
                        # If the agent didn't try to order later, we might just be informing.
                        # But we keep it as 'info' unless they tried to order.
                    except Exception:
                        pass

            logger.info(f"Agent response: action={action} order_id={order_id}")

            return {
                "response": final_message,
                "action": action,
                "order_id": order_id,
                "trace_url": None,
            }

        except Exception as e:
            logger.error(f"Agent execution error: {e}", exc_info=True)
            return {
                "response": "I encountered an error processing your request. Please try again.",
                "action": "error",
                "order_id": None,
                "trace_url": None,
            }


pharmacy_agent: Optional[PharmacyAgent] = None

def get_pharmacy_agent() -> PharmacyAgent:
    global pharmacy_agent
    if pharmacy_agent is None:
        pharmacy_agent = PharmacyAgent()
    return pharmacy_agent
