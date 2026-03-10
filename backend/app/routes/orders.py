"""
routes/orders.py — Order management API endpoints.

Routes:
    POST /orders/create            — Create a new order
    GET  /orders/user/{user_id}    — Get orders for a user
    GET  /orders/all               — Get all orders (admin only)

Prescription safety check is handled by the agent layer.
Direct API order creation also checks prescription_required.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Header
from fastapi.responses import FileResponse
from starlette.background import BackgroundTask
from sqlalchemy.orm import Session
from typing import List, Optional
import os

from app.database import get_db
from app.schemas.order import OrderCreate, OrderResponse
from app.services.order_service import create_order, get_user_orders, get_all_orders
from app.services.medicine_service import get_medicine_by_id
from app.services.export_service import export_orders_to_excel
from app.utils.security import verify_token

router = APIRouter(prefix="/orders", tags=["Orders"])


def _get_user_from_header(authorization: Optional[str] = Header(None), db: Session = Depends(get_db)):
    """
    Extract and verify JWT from Authorization header.

    Returns (user_id, role) tuple.
    """
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Authorization header required.")
    token = authorization.split(" ")[1]
    payload = verify_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid or expired token.")
    return payload


@router.post("/create", response_model=OrderResponse, status_code=201)
async def create_new_order(
    data: OrderCreate,
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db),
):
    """
    Create a new medicine order.

    Validates:
    - User is authenticated (JWT)
    - Medicine exists
    - Medicine does NOT require prescription (safety gate)
    - Sufficient stock is available

    Args:
        data: Order request (medicine_id, quantity)
        authorization: Bearer JWT token header
        db: Database session
    """
    payload = _get_user_from_header(authorization, db)
    user_id = payload.get("user_id")

    # Safety gate: check prescription requirement
    medicine = get_medicine_by_id(db, data.medicine_id)
    if medicine.prescription_required:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This medicine requires a prescription. Please upload prescription.",
        )

    return create_order(db, user_id, data.medicine_id, data.quantity)


@router.get("/all", response_model=List[OrderResponse])
async def list_all_orders(
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db),
):
    """
    Get all orders in the system. Admin only.

    Raises:
        403: If user is not an admin
    """
    payload = _get_user_from_header(authorization, db)
    if payload.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required.",
        )
    return get_all_orders(db)


@router.get("/export")
async def export_all_orders(
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db),
):
    """
    Export all orders to an Excel file. Admin only.
    """
    payload = _get_user_from_header(authorization, db)
    if payload.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required.",
        )
        
    file_path = export_orders_to_excel(db)
    return FileResponse(
        path=file_path, 
        filename="orders_export.xlsx", 
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        background=BackgroundTask(os.remove, file_path)
    )


@router.get("/user/{user_id}", response_model=List[OrderResponse])
async def list_user_orders(
    user_id: int,
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db),
):
    """
    Get all orders placed by a specific user.

    Users can only view their own orders. Admins can view any user's orders.

    Args:
        user_id: Target user's ID
        authorization: Bearer JWT token header
        db: Database session
    """
    payload = _get_user_from_header(authorization, db)
    requester_id = payload.get("user_id")
    requester_role = payload.get("role")

    # Authorization: User can only view own orders
    if requester_role != "admin" and requester_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only view your own orders.",
        )
    return get_user_orders(db, user_id)


@router.get("/export-user/{user_id}")
async def export_user_orders(
    user_id: int,
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db),
):
    """
    Export orders for a specific user to an Excel file.
    Users can only export their own orders; admins can export any user's orders.
    """
    payload = _get_user_from_header(authorization, db)
    requester_id = payload.get("user_id")
    requester_role = payload.get("role")

    if requester_role != "admin" and requester_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only export your own orders.",
        )

    from app.services.export_service import export_user_orders_to_excel
    file_path = export_user_orders_to_excel(db, user_id)
    return FileResponse(
        path=file_path,
        filename=f"my_orders_{user_id}.xlsx",
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        background=BackgroundTask(os.remove, file_path)
    )
