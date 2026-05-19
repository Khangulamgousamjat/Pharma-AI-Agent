"""
routes/orders.py — Order management API endpoints using Firestore.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Header
from fastapi.responses import FileResponse
from starlette.background import BackgroundTask
from typing import List, Optional, Any
import os

from app.firebase_db import get_db
from app.schemas.order import OrderCreate, OrderResponse
from app.services.order_service import create_order, get_user_orders, get_all_orders
from app.services.medicine_service import get_medicine_by_id
from app.services.export_service import export_orders_to_excel
from app.utils.security import verify_token

router = APIRouter(prefix="/orders", tags=["Orders"])


def _get_user_from_header(authorization: Optional[str] = Header(None), db: Any = Depends(get_db)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Authorization header required.")
    token = authorization.split(" ")[1]
    payload = verify_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid or expired token.")
    return payload


@router.post("/create", response_model=OrderResponse)
async def create_new_order(
    data: OrderCreate,
    db: Any = Depends(get_db),
    authorization: Optional[str] = Header(None),
):
    payload = _get_user_from_header(authorization, db)
    user_id = payload.get("user_id")

    medicine = get_medicine_by_id(db, data.medicine_id)
    if medicine.prescription_required:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This medicine requires a prescription. Please upload prescription.",
        )

    return create_order(db, user_id, data.medicine_id, data.quantity)


@router.get("/all", response_model=List[OrderResponse])
async def list_all_orders(
    db: Any = Depends(get_db),
    authorization: Optional[str] = Header(None),
):
    payload = _get_user_from_header(authorization, db)
    if payload.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required.",
        )
    return get_all_orders(db)


@router.get("/export")
async def export_all_orders(
    db: Any = Depends(get_db),
    authorization: Optional[str] = Header(None),
):
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
    user_id: str,
    db: Any = Depends(get_db),
    authorization: Optional[str] = Header(None),
):
    payload = _get_user_from_header(authorization, db)
    requester_id = payload.get("user_id")
    requester_role = payload.get("role")

    if requester_role != "admin" and requester_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only view your own orders.",
        )
    return get_user_orders(db, user_id)


@router.get("/export-user/{user_id}")
async def export_user_orders(
    user_id: str,
    db: Any = Depends(get_db),
    authorization: Optional[str] = Header(None),
):
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
