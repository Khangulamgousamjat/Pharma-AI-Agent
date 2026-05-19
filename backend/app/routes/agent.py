"""
routes/agent.py — AI Agent chat endpoint using Firestore.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Header
from typing import Optional, Any
import logging

from app.firebase_db import get_db
from app.schemas.agent import AgentChatRequest, AgentChatResponse
from app.agents.pharmacy_agent import get_pharmacy_agent
from app.utils.security import verify_token

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/agent", tags=["AI Agent"])


@router.post("/chat", response_model=AgentChatResponse)
async def agent_chat(
    request: AgentChatRequest,
    db: Any = Depends(get_db),
    authorization: Optional[str] = Header(None),
):
    """
    Send a message to the pharmacy AI agent.
    """
    # Validate JWT if provided
    if authorization:
        if authorization.startswith("Bearer "):
            token = authorization.split(" ")[1]
            payload = verify_token(token)
            if not payload:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid token.",
                )
            if payload.get("user_id") != request.user_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="User ID does not match token.",
                )

    agent = get_pharmacy_agent()

    logger.info(f"Agent chat: user={request.user_id} message='{request.message}'")

    result = await agent.chat(
        user_id=request.user_id,
        message=request.message,
        db=db,
    )

    response_text = result.get("response", "I'm sorry, I couldn't process your request.")
    if not isinstance(response_text, str):
        response_text = str(response_text)

    return AgentChatResponse(
        response=response_text,
        action=result.get("action"),
        order_id=result.get("order_id"),
        trace_url=result.get("trace_url"),
    )
