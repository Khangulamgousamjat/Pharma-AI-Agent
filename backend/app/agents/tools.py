"""
agents/tools.py — LangChain tool definitions for the Pharmacy Agent using Firestore.
"""

import json
import logging
from datetime import date
from typing import Any
from langchain_core.tools import tool

logger = logging.getLogger(__name__)

# Shared DB session — set before each agent invocation
_db_session = None


def set_db_session(db):
    """
    Set the database session for all tools to use.
    """
    global _db_session
    _db_session = db


@tool
def check_medicine_availability(medicine_name: str) -> str:
    """
    Search for a medicine by name and return its availability details.
    """
    from app.services.medicine_service import find_medicine_by_name

    if not _db_session:
        return json.dumps({"error": "Database not available. Please try again."})

    logger.info(f"[Tool] check_medicine_availability called for: {medicine_name}")
    medicine = find_medicine_by_name(_db_session, medicine_name)

    if not medicine:
        return json.dumps({
            "found": False,
            "message": f"Medicine '{medicine_name}' not found in our inventory.",
        })

    return json.dumps({
        "found": True,
        "id": medicine.id,
        "name": medicine.name,
        "stock": medicine.stock,
        "unit": medicine.unit,
        "price": medicine.price,
        "prescription_required": medicine.prescription_required,
        "expiry_date": str(medicine.expiry_date) if medicine.expiry_date else None,
        "description": medicine.description,
        "in_stock": medicine.stock > 0,
    })


@tool
def create_pharmacy_order(medicine_id: str, quantity: int, user_id: str) -> str:
    """
    Create a pharmacy order for the specified medicine and quantity.
    """
    from app.services.medicine_service import get_medicine_by_id
    from app.services.order_service import create_order
    from app.services.prescription_service import has_verified_prescription_for_medicine

    if not _db_session:
        return json.dumps({"error": "Database not available. Please try again."})

    logger.info(f"[Tool] create_pharmacy_order: medicine={medicine_id} qty={quantity} user={user_id}")

    try:
        medicine = get_medicine_by_id(_db_session, medicine_id)
    except Exception as e:
        return json.dumps({"error": f"Medicine not found: {str(e)}"})

    if medicine.expiry_date:
        today = date.today()
        # Handle if expiry_date is a datetime or string or date
        exp_date = medicine.expiry_date
        if isinstance(exp_date, str):
            exp_date = date.fromisoformat(exp_date)
        elif hasattr(exp_date, 'date'):
            exp_date = exp_date.date()
            
        if exp_date < today:
            logger.warning(
                f"[Safety] Expired medicine: {medicine.name} expired on {medicine.expiry_date}"
            )
            return json.dumps({
                "success": False,
                "action": "expired",
                "message": (
                    f"⚠️ '{medicine.name}' expired on {medicine.expiry_date}. "
                    "This medicine cannot be ordered. Please contact the pharmacy."
                ),
            })

    if medicine.prescription_required:
        has_rx = has_verified_prescription_for_medicine(
            _db_session, user_id, medicine.name
        )
        if not has_rx:
            logger.warning(
                f"[Safety] No verified prescription: user={user_id} medicine={medicine.name}"
            )
            return json.dumps({
                "success": False,
                "action": "prescription_required",
                "message": (
                    f"⚠️ '{medicine.name}' requires a valid prescription. "
                    "Please upload your prescription at /vision and wait for pharmacist approval. "
                    "Once verified, you can order this medicine through chat."
                ),
            })
        else:
            logger.info(
                f"[Safety] Verified prescription found for user={user_id} — allowing Rx order"
            )

    if medicine.stock < quantity:
        return json.dumps({
            "success": False,
            "action": "out_of_stock",
            "message": (
                f"Sorry, we only have {medicine.stock} {medicine.unit}(s) of "
                f"'{medicine.name}'. You requested {quantity}."
            ),
        })

    try:
        order = create_order(_db_session, user_id, medicine_id, quantity)
        return json.dumps({
            "success": True,
            "action": "order_created",
            "order_id": order.id,
            "medicine_name": medicine.name,
            "quantity": quantity,
            "unit": medicine.unit,
            "total_price": order.total_price,
            "status": order.status,
            "message": (
                f"✅ Order placed successfully! {quantity} {medicine.unit}(s) of "
                f"'{medicine.name}' for ₹{order.total_price:.2f}. Order ID: #{order.id}"
            ),
        })
    except Exception as e:
        logger.error(f"[Tool] Order creation failed: {e}")
        return json.dumps({"success": False, "action": "error", "message": str(e)})


@tool
def get_order_history(user_id: str) -> str:
    """
    Retrieve the recent order history for a user (last 5 orders).
    """
    from app.services.order_service import get_user_orders

    if not _db_session:
        return json.dumps({"error": "Database not available."})

    orders = get_user_orders(_db_session, user_id)
    if not orders:
        return json.dumps({"count": 0, "message": "No orders yet.", "orders": []})

    order_list = [
        {
            "order_id": o.id,
            "medicine_id": o.medicine_id,
            "quantity": o.quantity,
            "total_price": o.total_price,
            "status": o.status,
            "created_at": str(o.created_at),
        }
        for o in orders[:5]
    ]
    return json.dumps({"count": len(order_list), "orders": order_list})


@tool
def verify_prescription_tool(user_id: str, medicine_name: str) -> str:
    """
    Check whether a user has a pharmacist-verified prescription for a medicine.
    """
    from app.services.prescription_service import has_verified_prescription_for_medicine

    if not _db_session:
        return json.dumps({"error": "Database not available."})

    logger.info(f"[Tool] verify_prescription_tool: user={user_id} medicine='{medicine_name}'")
    has_rx = has_verified_prescription_for_medicine(_db_session, user_id, medicine_name)

    return json.dumps({
        "has_prescription": has_rx,
        "message": (
            f"✅ User has a verified prescription for '{medicine_name}'."
            if has_rx else
            f"❌ No verified prescription found for '{medicine_name}'. "
            "User must upload prescription at /vision and wait for pharmacist approval."
        ),
    })


@tool
def extract_medicine_from_image_tool(image_path: str) -> str:
    """
    Use the Vision Agent to extract medicine information from a prescription image.
    """
    import asyncio
    from app.agents.vision_agent import get_vision_agent

    logger.info(f"[Tool] extract_medicine_from_image_tool: path={image_path}")

    try:
        vision_agent = get_vision_agent()
        loop = asyncio.new_event_loop()
        result = loop.run_until_complete(vision_agent.extract(image_path))
        loop.close()
        return json.dumps(result)
    except Exception as e:
        return json.dumps({"success": False, "error": str(e)})


@tool
def predict_refill_tool(user_id: str) -> str:
    """
    Trigger the Refill Prediction Agent for a user.
    """
    import asyncio
    from app.agents.refill_agent import get_refill_agent

    if not _db_session:
        return json.dumps({"error": "Database not available."})

    logger.info(f"[Tool] predict_refill_tool: user={user_id}")

    try:
        refill_agent = get_refill_agent()
        loop = asyncio.new_event_loop()
        result = loop.run_until_complete(refill_agent.predict(_db_session, user_id))
        loop.close()
        return json.dumps({
            "alerts_created": result.alerts_created,
            "alerts_updated": result.alerts_updated,
            "message": result.message,
        })
    except Exception as e:
        return json.dumps({"success": False, "error": str(e)})


PHARMACY_TOOLS = [
    check_medicine_availability,
    create_pharmacy_order,
    get_order_history,
    verify_prescription_tool,
    extract_medicine_from_image_tool,
    predict_refill_tool,
]
