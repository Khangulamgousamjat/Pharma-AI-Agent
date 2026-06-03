"""
models/refill_alert.py — SQLAlchemy ORM model for Refill Alerts.

Phase 2 addition: Stores AI-predicted medicine refill dates.

The Refill Prediction Agent analyzes a user's order history,
estimates how fast they consume a medicine, and predicts when
they will run out — creating proactive refill alerts.

Status flow:
  pending   → alert created, user not yet notified
  notified  → user has viewed the alert in the UI
  ordered   → user clicked "Reorder" and a new order was created
"""

from sqlalchemy import Column, Integer, String, Date, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class RefillAlert(Base):
    """
    RefillAlert ORM model.

    Attributes:
        id: Primary key
        user_id: FK → users.id — patient this alert belongs to
        medicine_id: FK → medicines.id — medicine to refill
        predicted_refill_date: AI-predicted date when user will run out
        days_supply: Estimated days of supply from last order (used for calculation)
        status: Current state — 'pending', 'notified', or 'ordered'
        created_at: When the prediction was generated
    """

    __tablename__ = "refill_alerts"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    medicine_id = Column(Integer, ForeignKey("medicines.id"), nullable=False)

    # AI-predicted date when user will need a refill
    predicted_refill_date = Column(Date, nullable=True)

    # Days of supply estimated from last order quantity
    days_supply = Column(Integer, default=30, nullable=False)

    # Alert lifecycle status
    status = Column(String(20), default="pending", nullable=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    user = relationship("User", backref="refill_alerts")
    medicine = relationship("Medicine", backref="refill_alerts")

    def __repr__(self) -> str:
        return (
            f"<RefillAlert id={self.id} user={self.user_id} "
            f"medicine={self.medicine_id} date={self.predicted_refill_date} status={self.status}>"
        )
