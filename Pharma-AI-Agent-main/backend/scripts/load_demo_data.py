#!/usr/bin/env python3
"""
scripts/load_demo_data.py — Load demo data for hackathon judging.

Creates:
  - Demo user:       john@example.com / user123
  - Demo admin:      admin@pharmaagent.com / admin123  (if not exists)
  - Demo pharmacist: pharmacist@pharmaagent.com / pharma123 (if not exists)
  - 10 sample orders for the demo user

Usage:
    cd backend
    python scripts/load_demo_data.py
"""

import sys
import os

# Add parent dir to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import SessionLocal, init_db
from app.models.user import User
from app.models.medicine import Medicine
from app.models.order import Order
from app.utils.security import hash_password
from app.utils.seed_data import seed_medicines, seed_admin_user, seed_pharmacist_user

def create_demo_user(db):
    """Create demo user john@example.com / user123"""
    existing = db.query(User).filter(User.email == "john@example.com").first()
    if existing:
        print("✅ Demo user already exists: john@example.com")
        return existing

    user = User(
        name="John Demo",
        email="john@example.com",
        password_hash=hash_password("user123"),
        role="user",
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    print("✅ Demo user created: john@example.com / user123")
    return user


def create_demo_orders(db, user: User):
    """Create sample orders for the demo user"""
    existing_orders = db.query(Order).filter(Order.user_id == user.id).count()
    if existing_orders >= 5:
        print(f"✅ Demo orders already exist ({existing_orders} found)")
        return

    medicines = db.query(Medicine).filter(Medicine.prescription_required == False).limit(4).all()
    if not medicines:
        print("⚠️  No OTC medicines found — run the backend at least once first to seed medicines.")
        return

    sample_orders = [
        {"medicine": medicines[0], "quantity": 10, "status": "paid"},
        {"medicine": medicines[1], "quantity": 5,  "status": "confirmed"},
        {"medicine": medicines[0], "quantity": 20, "status": "paid"},
        {"medicine": medicines[2] if len(medicines) > 2 else medicines[0], "quantity": 2, "status": "pending"},
        {"medicine": medicines[3] if len(medicines) > 3 else medicines[1], "quantity": 3, "status": "confirmed"},
    ]

    for item in sample_orders:
        med = item["medicine"]
        qty = item["quantity"]
        order = Order(
            user_id=user.id,
            medicine_id=med.id,
            quantity=qty,
            total_price=round(med.price * qty, 2),
            status=item["status"],
        )
        db.add(order)

    db.commit()
    print(f"✅ Created {len(sample_orders)} demo orders for {user.email}")


def main():
    print("🚀 PharmaAgent AI — Loading demo data...")
    print("=" * 50)

    # Ensure all DB tables exist
    init_db()
    db = SessionLocal()

    try:
        # Seed medicines and default accounts
        seed_medicines(db)
        seed_admin_user(db)
        seed_pharmacist_user(db)

        # Create demo user and orders
        demo_user = create_demo_user(db)
        create_demo_orders(db, demo_user)

        print("=" * 50)
        print("✅ Demo data loaded successfully!\n")
        print("🔑 Demo Credentials:")
        print("   User:       john@example.com / user123")
        print("   Admin:      admin@pharmaagent.com / admin123")
        print("   Pharmacist: pharmacist@pharmaagent.com / pharma123")
        print("\n🌐 Open http://localhost:3000 to start the demo.")
    finally:
        db.close()


if __name__ == "__main__":
    main()
