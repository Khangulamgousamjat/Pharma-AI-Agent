"""
models/webhook_event.py — SQLAlchemy ORM model for webhook fulfillment events.

Phase 3 addition: Tracks every attempt to notify the fulfillment warehouse
about a new order. Enables retry visibility, audit trail, and admin re-trigger.

Status lifecycle:
  pending   → webhook queued / in-flight
  success   → warehouse acknowledged (HTTP 2xx)
  failed    → all retries exhausted (HTTP error or timeout)
  retrying  → new manual retrigger initiated (admin action)
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class WebhookEvent(Base):
    """
    WebhookEvent ORM model.

    One record is created per webhook attempt (initial + each retry).
    Total attempts for an order = count of rows where order_id matches.

    Attributes:
        id: Primary key
        order_id: FK → orders.id — which order triggered the webhook
        attempt_number: 1-indexed attempt count (1 = initial, 2..N = retries)
        status: 'pending' | 'success' | 'failed' | 'retrying'
        idempotency_key: Value sent as X-Idempotency-Key header
        request_payload: JSON string of what was sent to the warehouse
        response_body: JSON/text response from warehouse (or error message)
        http_status_code: HTTP response code (None if network error)
        created_at: When this attempt was made
    """

    __tablename__ = "webhook_events"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False, index=True)
    attempt_number = Column(Integer, default=1, nullable=False)

    # Fulfillment status
    status = Column(String(20), default="pending", nullable=False)

    # Idempotency — same key across all retries for the same order
    idempotency_key = Column(String(100), nullable=True)

    # Full request payload sent to warehouse (stored for debugging)
    request_payload = Column(Text, nullable=True)

    # Response from warehouse (HTTP body or error message)
    response_body = Column(Text, nullable=True)

    # HTTP status code (None if timeout/connection refused)
    http_status_code = Column(Integer, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationship
    order = relationship("Order", backref="webhook_events")

    def __repr__(self) -> str:
        return (
            f"<WebhookEvent id={self.id} order={self.order_id} "
            f"attempt={self.attempt_number} status={self.status}>"
        )
