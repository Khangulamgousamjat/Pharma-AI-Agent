from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Annotated

from app.database import get_db
from app.models.user import User
from app.schemas.user import UserResponse
from app.services.auth_service import get_current_user_from_token

router = APIRouter(prefix="/admin", tags=["Admin Management"])

def check_admin_role(user: User = Depends(get_current_user_from_token)):
    if user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied. Admin role required."
        )
    return user

@router.get("/pharmacists/pending", response_model=List[UserResponse])
async def get_pending_pharmacists(
    db: Annotated[Session, Depends(get_db)],
    admin: User = Depends(check_admin_role)
):
    """Fetch all pharmacists awaiting approval."""
    return db.query(User).filter(User.role == "pharmacist", User.is_approved == 0).all()

@router.post("/pharmacists/{user_id}/approve", status_code=200)
async def approve_pharmacist(
    user_id: int,
    db: Annotated[Session, Depends(get_db)],
    admin: User = Depends(check_admin_role)
):
    """Approve a pending pharmacist account."""
    user = db.query(User).filter(User.id == user_id, User.role == "pharmacist").first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pharmacist not found."
        )
    
    user.is_approved = 1
    db.commit()
    return {"message": f"Pharmacist {user.email} approved successfully."}
