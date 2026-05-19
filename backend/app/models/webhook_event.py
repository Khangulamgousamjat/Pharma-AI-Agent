"""
models/webhook_event.py — Firestore schema for the Webhook Events collection.
"""

from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional

class WebhookEvent(BaseModel):
    """
    WebhookEvent Firestore document schema.
    """
    id: str = Field(description="Firestore Document ID")
    order_id: str
    attempt_number: int = 1
    status: str = "pending"
    idempotency_key: Optional[str] = None
    request_payload: Optional[str] = None
    response_body: Optional[str] = None
    http_status_code: Optional[int] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

    def to_dict(self):
        return self.model_dump(exclude={'id'})
