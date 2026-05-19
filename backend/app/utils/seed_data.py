"""
utils/seed_data.py — Seed initial medicine inventory and default users into Firebase.

Run on application startup to ensure Firestore has sample medicines
and Firebase Auth has default accounts.
"""

from datetime import date, datetime
import logging
from firebase_admin import auth as firebase_auth, firestore

logger = logging.getLogger(__name__)

SEED_MEDICINES = [
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


def seed_medicines(db: firestore.Client) -> None:
    seeded_count = 0
    for med_data in SEED_MEDICINES:
        existing = db.collection("medicines").where("name", "==", med_data["name"]).limit(1).get()
        if not existing:
            med_dict = med_data.copy()
            if isinstance(med_dict.get("expiry_date"), date):
                med_dict["expiry_date"] = datetime.combine(med_dict["expiry_date"], datetime.min.time())
            
            doc_ref = db.collection("medicines").document()
            med_dict["id"] = doc_ref.id
            doc_ref.set(med_dict)
            seeded_count += 1

    if seeded_count > 0:
        logger.info(f"Seeded {seeded_count} medicines into Firestore.")
    else:
        logger.info("Medicine seed data already present in Firestore, skipping.")


def _seed_auth_and_firestore_user(db: firestore.Client, email: str, password: str, name: str, role: str, is_approved: bool) -> None:
    try:
        user_record = firebase_auth.get_user_by_email(email)
        uid = user_record.uid
    except firebase_auth.UserNotFoundError:
        user_record = firebase_auth.create_user(
            email=email,
            password=password,
            display_name=name
        )
        uid = user_record.uid
        logger.info(f"Created Firebase Auth user: {email} (uid={uid})")

    # Set role claim
    firebase_auth.set_custom_user_claims(uid, {"role": role})

    # Sync to Firestore using the uid as the document ID
    doc_ref = db.collection("users").document(uid)
    doc = doc_ref.get()
    if not doc.exists:
        doc_ref.set({
            "id": uid,
            "name": name,
            "email": email,
            "role": role,
            "is_approved": is_approved,
            "ui_theme": "dark",
            "preferred_language": "en",
            "created_at": firestore.SERVER_TIMESTAMP
        })
        logger.info(f"Created Firestore profile for user: {email} (uid={uid})")
    else:
        doc_ref.update({
            "name": name,
            "role": role,
            "is_approved": is_approved
        })
        logger.info(f"Updated Firestore profile for user: {email} (uid={uid})")


def seed_admin_user(db: firestore.Client) -> None:
    _seed_auth_and_firestore_user(
        db=db,
        email="admin@gmail.com",
        password="Kingkhan@12",
        name="Admin",
        role="admin",
        is_approved=True
    )


def seed_pharmacist_user(db: firestore.Client) -> None:
    _seed_auth_and_firestore_user(
        db=db,
        email="pharmacist@pharmaagent.com",
        password="pharma123",
        name="Dr. Pharmacist",
        role="pharmacist",
        is_approved=True
    )


def seed_demo_user(db: firestore.Client) -> None:
    _seed_auth_and_firestore_user(
        db=db,
        email="john@example.com",
        password="user123",
        name="John Demo",
        role="user",
        is_approved=True
    )
