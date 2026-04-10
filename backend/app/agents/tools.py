"""
agents/tools.py — LangChain tool definitions for the Pharmacy Agent.

Phase 1 tools:
    - check_medicine_availability: retrieves medicine info incl. prescription_required
    - create_pharmacy_order: prescription gate + stock gate (Phase 2: + expiry + verified Rx)
    - get_order_history: retrieves user's recent orders

Phase 2 NEW tools:
    - verify_prescription_tool: checks if user has a pharmacist-verified prescription
    - extract_medicine_from_image_tool: calls Vision Agent on an image path
    - predict_refill_tool: runs Refill Agent for a user

ENHANCED SAFETY LOGIC (Phase 2):
    create_pharmacy_order now enforces THREE checks (was two):
      1. EXPIRY CHECK: medicine.expiry_date must be today or in the future
      2. PRESCRIPTION CHECK (Rx): if prescription_required=True →
         check if user has verified prescription first;
         if yes → allow; if no → block with upload request
      3. STOCK CHECK: sufficient quantity must be in inventory
"""

import json
import logging
from datetime import date
from langchain_core.tools import tool

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Shared DB session — set before each agent invocation
# ---------------------------------------------------------------------------
_db_session = None


def set_db_session(db):
    """
    Set the database session for all tools to use.

    Called by pharmacy_agent.py before invoking the agent executor.

    Args:
        db: SQLAlchemy Session object
    """
    global _db_session
    _db_session = db


# ===========================================================================
# TOOL 1: Check Medicine Availability  (Phase 1 — unchanged)
# ===========================================================================
@tool
def check_medicine_availability(medicine_name: str) -> str:
    """
    Search for a medicine by name and return its availability details.

    Use this tool FIRST when the user asks about any medicine to check:
    - Whether it exists in our pharmacy inventory
    - Current stock levels
    - Price per unit
    - Whether it requires a prescription (prescription_required)
    - Expiry date (important for Phase 2 safety checks)

    Args:
        medicine_name: The name or partial name of the medicine to search for.
                       Example: 'paracetamol', 'amoxicillin', 'cough syrup'

    Returns:
        JSON string with medicine details or error message.
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


# ===========================================================================
# TOOL 2: Create Pharmacy Order  (Phase 2 — ENHANCED SAFETY)
# ===========================================================================
@tool
def create_pharmacy_order(medicine_id: int, quantity: int, user_id: int) -> str:
    """
    Create a pharmacy order for the specified medicine and quantity.

    ENHANCED SAFETY RULES (Phase 2) — enforce in this order:
    1. EXPIRY CHECK: if medicine.expiry_date < today → REJECT (never dispense expired medicine)
    2. PRESCRIPTION CHECK: if prescription_required=True:
       a. Call verify_prescription_tool(user_id, medicine_name) first
       b. If user has a pharmacist-verified prescription → allow the order
       c. If no verified prescription → REJECT and ask user to upload prescription
    3. STOCK CHECK: if medicine.stock < quantity → REJECT

    Args:
        medicine_id: The integer ID of the medicine.
        quantity: Number of units to order (must be >= 1).
        user_id: The ID of the user placing the order.

    Returns:
        JSON string confirming order creation or explaining the block reason.
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

    # -----------------------------------------------------------------------
    # SAFETY CHECK 1: EXPIRY DATE ENFORCEMENT (Phase 2)
    # Never allow dispensing of expired medicines.
    # -----------------------------------------------------------------------
    if medicine.expiry_date:
        today = date.today()
        if medicine.expiry_date < today:
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

    # -----------------------------------------------------------------------
    # SAFETY CHECK 2: PRESCRIPTION ENFORCEMENT (Phase 2 upgraded)
    # Phase 1: always reject Rx medicines
    # Phase 2: check if user has a pharmacist-VERIFIED prescription first
    # -----------------------------------------------------------------------
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

    # -----------------------------------------------------------------------
    # SAFETY CHECK 3: STOCK AVAILABILITY
    # -----------------------------------------------------------------------
    if medicine.stock < quantity:
        return json.dumps({
            "success": False,
            "action": "out_of_stock",
            "message": (
                f"Sorry, we only have {medicine.stock} {medicine.unit}(s) of "
                f"'{medicine.name}'. You requested {quantity}."
            ),
        })

    # -----------------------------------------------------------------------
    # All safety checks passed — create order
    # -----------------------------------------------------------------------
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


# ===========================================================================
# TOOL 3: Get Order History  (Phase 1 — unchanged)
# ===========================================================================
@tool
def get_order_history(user_id: int) -> str:
    """
    Retrieve the recent order history for a user.

    Use when the user asks 'what did I order?' or 'show my orders'.

    Args:
        user_id: The ID of the user whose orders to retrieve.

    Returns:
        JSON string with list of recent orders (last 5).
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


# ===========================================================================
# TOOL 4: Verify Prescription  (Phase 2 NEW)
# ===========================================================================
@tool
def verify_prescription_tool(user_id: int, medicine_name: str) -> str:
    """
    Check whether a user has a pharmacist-verified prescription for a medicine.

    Use this tool BEFORE attempting to create an order for any Rx medicine.
    Do not assume the user has or doesn't have a prescription — always check.

    Args:
        user_id: The user's ID.
        medicine_name: Name of the Rx medicine being checked.

    Returns:
        JSON with has_prescription (bool) and a status message.
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


# ===========================================================================
# TOOL 5: Extract Medicine from Image  (Phase 2 NEW)
# ===========================================================================
@tool
def extract_medicine_from_image_tool(image_path: str) -> str:
    """
    Use the Vision Agent to extract medicine information from a prescription image.

    Use this tool when the user says they have a prescription image they'd
    like to upload, or when you need to process a prescription image path.

    NOTE: This tool is for the agent to call after an image has already
    been uploaded and saved to disk. The image_path must be a valid file path.

    Args:
        image_path: Absolute path to a prescription image file.

    Returns:
        JSON with extracted medicine_name, dosage, quantity, and confidence.
    """
    import asyncio
    from app.agents.vision_agent import get_vision_agent

    logger.info(f"[Tool] extract_medicine_from_image_tool: path={image_path}")

    try:
        vision_agent = get_vision_agent()
        # Run async function synchronously inside tool
        loop = asyncio.new_event_loop()
        result = loop.run_until_complete(vision_agent.extract(image_path))
        loop.close()
        return json.dumps(result)
    except Exception as e:
        return json.dumps({"success": False, "error": str(e)})


# ===========================================================================
# TOOL 6: Predict Refill  (Phase 2 NEW)
# ===========================================================================
@tool
def predict_refill_tool(user_id: int) -> str:
    """
    Trigger the Refill Prediction Agent for a user.

    Analyzes the user's order history and creates refill alerts for medicines
    they are likely to run out of soon (within 7 days).

    Use when the user asks about refills, or proactively after an order.

    Args:
        user_id: The user ID to run prediction for.

    Returns:
        JSON with alerts_created, alerts_updated, and a message.
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


# ===========================================================================
# Tool Registry
# ===========================================================================
PHARMACY_TOOLS = [
    check_medicine_availability,
    create_pharmacy_order,
    get_order_history,
    verify_prescription_tool,        # Phase 2
    extract_medicine_from_image_tool, # Phase 2
    predict_refill_tool,             # Phase 2
]
