"""
models/user.py — SQLAlchemy ORM model for the Users table.

Roles: 'user' (default), 'admin', 'pharmacist' (Phase 2+).
Phase 3: adds ui_theme + preferred_language for settings persistence.
"""

from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class User(Base):
    """
    User ORM model.

    Attributes:
        id: Primary key
        name: Display name
        email: Unique login email
        password_hash: bcrypt hash (never store plaintext)
        role: 'user' | 'admin' | 'pharmacist'
        ui_theme: 'dark' | 'light' — persisted UI preference (Phase 3)
        preferred_language: ISO code — 'en' | 'hi' | 'mr' (Phase 3)
        is_approved: True for users/admin, False for unapproved pharmacists
        created_at: Account creation timestamp
        created_at: Account creation timestamp
    """

    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(20), default="user", nullable=False)
    is_approved = Column(Integer, default=1, server_default="1", nullable=False) # 1 = True, 0 = False. We use Integer for SQLite compatibility with booleans.

    # Phase 3: UI personalisation — stored in DB + synced to localStorage on login
    ui_theme = Column(String(10), default="dark", nullable=False)
    preferred_language = Column(String(10), default="en", nullable=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    orders = relationship("Order", back_populates="user", lazy="dynamic")

    def __repr__(self) -> str:
        return f"<User id={self.id} email={self.email} role={self.role}>"
