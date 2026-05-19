from fastapi import APIRouter, Depends, HTTPException, status, Header
from typing import List, Any, Optional

from app.firebase_db import get_db
from app.schemas.user import UserResponse
from app.utils.security import verify_token

router = APIRouter(prefix="/admin", tags=["Admin Management"])

def check_admin_role(authorization: Optional[str] = Header(None)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization header missing or invalid.",
        )
    token = authorization.split(" ")[1]
    payload = verify_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token.",
        )
    if payload.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied. Admin role required."
        )
    return payload

@router.get("/pharmacists/pending", response_model=List[UserResponse])
async def get_pending_pharmacists(
    db: Any = Depends(get_db),
    admin: dict = Depends(check_admin_role)
):
    """Fetch all pharmacists awaiting approval."""
    docs = db.collection("users").where("role", "==", "pharmacist").stream()
    pending = []
    for doc in docs:
        data = doc.to_dict()
        data['id'] = doc.id
        if not data.get("is_approved", False):
            pending.append(UserResponse(**data))
    return pending

@router.post("/pharmacists/{user_id}/approve", status_code=200)
async def approve_pharmacist(
    user_id: str,
    db: Any = Depends(get_db),
    admin: dict = Depends(check_admin_role)
):
    """Approve a pending pharmacist account."""
    doc_ref = db.collection("users").document(user_id)
    doc = doc_ref.get()
    if not doc.exists:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pharmacist not found."
        )
    
    doc_ref.update({"is_approved": True})
    return {"message": f"Pharmacist approved successfully."}
