"""
utils/seed_data.py — Seed initial medicine inventory into the database.

Run on application startup to ensure the database has sample medicines
for testing and demonstration. Uses upsert logic (skip if already exists).
"""

from sqlalchemy.orm import Session
from datetime import date
import logging

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Sample Medicine Catalogue
# ---------------------------------------------------------------------------
# Medicines are split into:
#   - OTC (Over The Counter): prescription_required = False → agent allows order
#   - Rx (Prescription):      prescription_required = True  → agent rejects order
# ---------------------------------------------------------------------------
SEED_MEDICINES = [
    # OTC Medicines — agent can order these freely
    {
        "name": "Paracetamol 500mg",
        "stock": 500,
        "unit": "tablets",
        "price": 5.0,
        "prescription_required": False,
        "expiry_date": date(2026, 12, 31),
        "description": "Fever and pain relief. OTC medicine.",
    },
    {
        "name": "Ibuprofen 400mg",
        "stock": 300,
        "unit": "tablets",
        "price": 8.0,
        "prescription_required": False,
        "expiry_date": date(2026, 10, 31),
        "description": "Anti-inflammatory and pain relief. OTC.",
    },
    {
        "name": "Cetirizine 10mg",
        "stock": 200,
        "unit": "tablets",
        "price": 6.0,
        "prescription_required": False,
        "expiry_date": date(2026, 8, 31),
        "description": "Antihistamine for allergies. OTC.",
    },
    {
        "name": "Cough Syrup 100ml",
        "stock": 150,
        "unit": "bottles",
        "price": 45.0,
        "prescription_required": False,
        "expiry_date": date(2026, 6, 30),
        "description": "Relieves dry and productive coughs. OTC.",
    },
    {
        "name": "Vitamin C 1000mg",
        "stock": 400,
        "unit": "tablets",
        "price": 12.0,
        "prescription_required": False,
        "expiry_date": date(2027, 1, 31),
        "description": "Immunity booster. OTC supplement.",
    },
    {
        "name": "Antacid Tablets",
        "stock": 250,
        "unit": "tablets",
        "price": 4.0,
        "prescription_required": False,
        "expiry_date": date(2026, 9, 30),
        "description": "Relieves heartburn and indigestion. OTC.",
    },
    {
        "name": "ORS Sachets",
        "stock": 100,
        "unit": "sachets",
        "price": 10.0,
        "prescription_required": False,
        "expiry_date": date(2026, 12, 31),
        "description": "Oral rehydration salts for dehydration. OTC.",
    },
    # Rx Medicines — agent will reject without prescription
    {
        "name": "Amoxicillin 500mg",
        "stock": 200,
        "unit": "capsules",
        "price": 25.0,
        "prescription_required": True,
        "expiry_date": date(2026, 5, 31),
        "description": "Antibiotic. Prescription required.",
    },
    {
        "name": "Metformin 500mg",
        "stock": 180,
        "unit": "tablets",
        "price": 15.0,
        "prescription_required": True,
        "expiry_date": date(2026, 11, 30),
        "description": "Diabetes management. Prescription required.",
    },
    {
        "name": "Atorvastatin 20mg",
        "stock": 120,
        "unit": "tablets",
        "price": 35.0,
        "prescription_required": True,
        "expiry_date": date(2026, 7, 31),
        "description": "Cholesterol management. Prescription required.",
    },
]


def seed_medicines(db: Session) -> None:
    """
    Seed the medicines table with sample data.

    Skips medicines that already exist (by name) to prevent duplicates.
    Safe to call on every startup.

    Args:
        db: SQLAlchemy database session
    """
    from app.models.medicine import Medicine

    seeded_count = 0
    for med_data in SEED_MEDICINES:
        # Check if medicine already exists by name
        existing = db.query(Medicine).filter(Medicine.name == med_data["name"]).first()
        if not existing:
            medicine = Medicine(**med_data)
            db.add(medicine)
            seeded_count += 1

    if seeded_count > 0:
        db.commit()
        logger.info(f"Seeded {seeded_count} medicines into database.")
    else:
        logger.info("Medicine seed data already present, skipping.")


def seed_admin_user(db: Session) -> None:
    """
    Create a default admin user if none exists.

    Admin credentials:
        Email: admin@pharmaagent.com
        Password: admin123

    Args:
        db: SQLAlchemy database session
    """
    from app.models.user import User
    from app.utils.security import hash_password

    existing_admin = db.query(User).filter(User.role == "admin").first()
    if not existing_admin:
        admin = User(
            name="Admin",
            email="Admin12",
            password_hash=hash_password("Kingkhan@12"),
            role="admin",
            is_approved=1
        )
        db.add(admin)
        db.commit()
        logger.info("Default admin user created: admin@pharmaagent.com / admin123")
    else:
        logger.info("Admin user already exists, skipping.")


def seed_pharmacist_user(db: Session) -> None:
    """
    Phase 2: Create a default pharmacist user if none exists.

    Pharmacist credentials:
        Email: pharmacist@pharmaagent.com
        Password: pharma123

    The pharmacist can:
      - View pending prescriptions (GET /pharmacist/prescriptions/pending)
      - Approve prescriptions (POST /pharmacist/prescriptions/{id}/verify)

    Args:
        db: SQLAlchemy database session
    """
    from app.models.user import User
    from app.utils.security import hash_password

    existing = db.query(User).filter(User.email == "pharmacist@pharmaagent.com").first()
    if not existing:
        pharmacist = User(
            name="Dr. Pharmacist",
            email="pharmacist@pharmaagent.com",
            password_hash=hash_password("pharma123"),
            role="pharmacist",
            is_approved=1
        )
        db.add(pharmacist)
        db.commit()
        logger.info("Default pharmacist user created: pharmacist@pharmaagent.com / pharma123")
    else:
        logger.info("Pharmacist user already exists, skipping.")


def seed_demo_user(db: Session) -> None:
    """
    Create a default demo user (regular user role) if none exists.

    Demo credentials:
        Email: john@example.com
        Password: user123

    Used for the "user" role tab on the login page.
    """
    from app.models.user import User
    from app.utils.security import hash_password

    existing = db.query(User).filter(User.email == "john@example.com").first()
    if not existing:
        demo_user = User(
            name="John Demo",
            email="john@example.com",
            password_hash=hash_password("user123"),
            role="user",
            is_approved=1
        )
        db.add(demo_user)
        db.commit()
        logger.info("Demo user created: john@example.com / user123")
    else:
        logger.info("Demo user already exists, skipping.")

