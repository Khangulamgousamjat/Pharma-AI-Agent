"""
schemas/agent.py — Pydantic schemas for AI Agent chat API.
"""

from pydantic import BaseModel, Field
from typing import Optional


class AgentChatRequest(BaseModel):
    """
    Input schema for POST /agent/chat.

    The agent receives the user's natural language message and their user_id
    so it can create orders on their behalf.
    """
    user_id: int = Field(..., description="Authenticated user ID")
    message: str = Field(..., min_length=1, description="User's natural language pharmacy request")


class AgentChatResponse(BaseModel):
    """
    Output schema for POST /agent/chat.

    action: One of 'order_created', 'prescription_required', 'info', 'error'
    trace_url: Optional LangSmith trace URL for observability
    """
    response: str
    action: Optional[str] = None   # e.g. "order_created", "prescription_required"
    order_id: Optional[int] = None
    trace_url: Optional[str] = None


class PaymentRequest(BaseModel):
    """Schema for POST /payment/process."""
    order_id: int
    amount: float
    payment_method: str = Field(default="card", description="Payment method (card, upi, cash)")


class PaymentResponse(BaseModel):
    """Schema for payment response."""
    status: str = "success"
    transaction_id: str
    message: str
    order_id: int
