"""
routes/medicines.py — Medicine inventory API endpoints.

Routes:
    GET /medicines           — List all medicines
    GET /medicines/search    — Search medicines by name query
    GET /medicines/{id}      — Get a single medicine by ID

Used by the AI agent to look up medicine details during order processing.
"""

from fastapi import APIRouter, Depends, Query, Header, HTTPException, status
from fastapi.responses import FileResponse
from starlette.background import BackgroundTask
from sqlalchemy.orm import Session
from typing import List, Optional
import os

from app.database import get_db
from app.schemas.medicine import MedicineResponse
from app.services.medicine_service import (
    get_all_medicines,
    get_medicine_by_id,
    search_medicines,
)
from app.utils.security import verify_token

router = APIRouter(prefix="/medicines", tags=["Medicines"])


@router.get("", response_model=List[MedicineResponse])
async def list_medicines(db: Session = Depends(get_db)):
    """
    Get all medicines in the inventory.

    Returns complete list sorted by name, including stock levels
    and prescription_required flags.
    """
    return get_all_medicines(db)


@router.get("/search", response_model=List[MedicineResponse])
async def search(
    q: str = Query(..., min_length=1, description="Search term for medicine name"),
    db: Session = Depends(get_db),
):
    """
    Search medicines by name (partial, case-insensitive match).

    Args:
        q: Search query string
        db: Database session

    Example:
        GET /medicines/search?q=para  → returns Paracetamol medicines
    """
    return search_medicines(db, q)


@router.get("/{medicine_id}", response_model=MedicineResponse)
async def get_medicine(medicine_id: int, db: Session = Depends(get_db)):
    """
    Get a single medicine by its ID.

    Args:
        medicine_id: Medicine primary key
        db: Database session

    Raises:
        404: If medicine not found
    """
    return get_medicine_by_id(db, medicine_id)


@router.get("/export")
async def export_inventory(
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db),
):
    """
    Export full medicine inventory as Excel. Admin or Pharmacist only.
    """
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Authorization required.")
    token = authorization.split(" ")[1]
    payload = verify_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid or expired token.")
    if payload.get("role") not in ("admin", "pharmacist"):
        raise HTTPException(status_code=403, detail="Admin or Pharmacist access required.")

    from app.services.export_service import export_inventory_to_excel
    file_path = export_inventory_to_excel(db)
    return FileResponse(
        path=file_path,
        filename="medicine_inventory.xlsx",
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        background=BackgroundTask(os.remove, file_path)
    )
