"""
routes/agent.py — AI Agent chat endpoint.

Route:
    POST /agent/chat — Send a message to the pharmacy AI agent

The agent understands natural language, finds medicines,
validates prescription requirements, and creates orders.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Header
from sqlalchemy.orm import Session
from typing import Optional, Annotated
import logging

from app.database import get_db
from app.schemas.agent import AgentChatRequest, AgentChatResponse
from app.agents.pharmacy_agent import get_pharmacy_agent
from app.utils.security import verify_token

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/agent", tags=["AI Agent"])


@router.post("/chat", response_model=AgentChatResponse)
async def agent_chat(
    request: AgentChatRequest,
    db: Annotated[Session, Depends(get_db)],
    authorization: Optional[str] = Header(None),
):
    """
    Send a message to the pharmacy AI agent.

    The agent will:
    1. Parse the user's natural language request
    2. Search for the requested medicine
    3. Check prescription requirements (safety gate)
    4. Create an order if medicine is OTC
    5. Return a human-friendly response

    The agent is traced in LangSmith — all reasoning steps are visible
    in the LangSmith dashboard under project 'pharmaagent-ai'.

    Args:
        request: Chat request containing user_id and message
        authorization: Optional Bearer JWT token
        db: Database session

    Returns:
        AgentChatResponse: Agent's response, action type, and optional order ID

    Example:
        POST /agent/chat
        {"user_id": 1, "message": "I need 2 paracetamol tablets"}
        → {"response": "✅ Order placed...", "action": "order_created", "order_id": 42}
    """
    # Validate JWT if provided (optional for testing, required in production)
    if authorization:
        if authorization.startswith("Bearer "):
            token = authorization.split(" ")[1]
            payload = verify_token(token)
            if not payload:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid token.",
                )
            # Verify user_id matches token (prevent order spoofing)
            if payload.get("user_id") != request.user_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="User ID does not match token.",
                )

    # Get the singleton pharmacy agent
    agent = get_pharmacy_agent()

    logger.info(f"Agent chat: user={request.user_id} message='{request.message}'")

    # Run the agent (async — does not block the event loop)
    result = await agent.chat(
        user_id=request.user_id,
        message=request.message,
        db=db,
    )

    # Ensure response is always a string (Pydantic requires str)
    response_text = result.get("response", "I'm sorry, I couldn't process your request.")
    if not isinstance(response_text, str):
        response_text = str(response_text)

    return AgentChatResponse(
        response=response_text,
        action=result.get("action"),
        order_id=result.get("order_id"),
        trace_url=result.get("trace_url"),
    )
