"""
models/order.py — SQLAlchemy ORM model for the Orders table.

Records every medicine order placed by users through the AI agent or directly.
"""

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Float
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class OrderStatus(str):
    """Order status constants."""
    PENDING = "pending"
    CONFIRMED = "confirmed"
    CANCELLED = "cancelled"
    PAID = "paid"


class Order(Base):
    """
    Order ORM model.

    Attributes:
        id: Primary key, auto-increment
        user_id: FK referencing Users.id — who placed the order
        medicine_id: FK referencing Medicines.id — what was ordered
        quantity: Number of units ordered
        total_price: Calculated total (quantity × medicine.price)
        status: Current state of the order (pending/confirmed/paid/cancelled)
        created_at: Timestamp of order creation (auto-set)
    """

    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    medicine_id = Column(Integer, ForeignKey("medicines.id"), nullable=False)
    quantity = Column(Integer, default=1, nullable=False)
    total_price = Column(Float, default=0.0, nullable=False)
    status = Column(String(20), default="pending", nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships for easy joins
    user = relationship("User", back_populates="orders")
    medicine = relationship("Medicine", back_populates="orders")

    def __repr__(self) -> str:
        return f"<Order id={self.id} user={self.user_id} medicine={self.medicine_id} status={self.status}>"
