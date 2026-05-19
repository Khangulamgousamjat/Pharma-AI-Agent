"""
database.py — Forwarding proxy to firebase_db.py for backwards compatibility.
All SQLAlchemy / PostgreSQL legacy code has been removed.
"""

from app.firebase_db import get_db, init_firebase
