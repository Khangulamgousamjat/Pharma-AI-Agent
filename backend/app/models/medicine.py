"""
models/medicine.py — SQLAlchemy ORM model for the Medicines table.

Tracks medicine inventory. The `prescription_required` flag is critical —
it is used by the AI agent safety logic to allow or block orders.
"""

from sqlalchemy import Column, Integer, String, Boolean, Date, Float
from sqlalchemy.orm import relationship
from app.database import Base


class Medicine(Base):
    """
    Medicine ORM model.

    Attributes:
        id: Primary key, auto-increment
        name: Medicine name (e.g., 'Paracetamol 500mg')
        stock: Current quantity in inventory
        unit: Unit of measure (e.g., 'tablets', 'bottles')
        price: Price per unit
        prescription_required: If True, agent will reject order without prescription upload
        expiry_date: Expiry date of current stock batch
        description: Brief description of the medicine
    """

    __tablename__ = "medicines"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(200), unique=True, index=True, nullable=False)
    stock = Column(Integer, default=0, nullable=False)
    unit = Column(String(50), default="tablets", nullable=False)
    price = Column(Float, default=0.0, nullable=False)

    # SAFETY-CRITICAL FIELD: used by AI agent to enforce prescription logic
    prescription_required = Column(Boolean, default=False, nullable=False)

    expiry_date = Column(Date, nullable=True)
    description = Column(String(500), nullable=True)

    # Relationship: one medicine can appear in many orders
    orders = relationship("Order", back_populates="medicine", lazy="dynamic")

    def __repr__(self) -> str:
        return f"<Medicine id={self.id} name={self.name} stock={self.stock} rx={self.prescription_required}>"
