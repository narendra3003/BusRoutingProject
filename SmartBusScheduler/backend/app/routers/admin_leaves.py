from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from typing import List, Optional

from ..database import get_db
from ..models import DriverLeave, Driver, User
from ..schemas import LeaveResponse, MessageResponse
from .auth import get_current_user, check_admin


router = APIRouter()


# =====================================================
# HELPER FUNCTION
# =====================================================

def format_leave(leave: DriverLeave, driver_name: str) -> dict:
    """Formats leave data to match frontend expectations."""
    return {
        "id": leave.id,
        "driver_id": leave.driver_id,
        "driver_name": driver_name,
        "start_date": leave.start_date,
        "end_date": leave.end_date,
        "reason": leave.reason,
        "status": leave.status,
        "created_at": leave.created_at,
    }


# =====================================================
# GET LEAVES
# =====================================================

@router.get("/", response_model=List[LeaveResponse])
def get_driver_leaves(
    status: Optional[str] = Query(
        None,
        description="Filter by status: pending, granted, rejected"
    ),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    Fetch driver leave requests with optional status filtering.
    Accessible only by admins.
    """
    check_admin(current_user)

    query = (
        db.query(DriverLeave, User.name.label("driver_name"))
        .join(Driver, DriverLeave.driver_id == Driver.user_id)
        .join(User, Driver.user_id == User.id)
    )

    if status:
        query = query.filter(DriverLeave.status == status)

    leaves = query.order_by(DriverLeave.id.desc()).all()

    return [
        format_leave(leave, driver_name)
        for leave, driver_name in leaves
    ]


# =====================================================
# APPROVE LEAVE
# =====================================================

@router.put("/{leave_id}/approve", response_model=MessageResponse)
def approve_leave(
    leave_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Approve a pending leave request."""
    check_admin(current_user)

    leave = db.query(DriverLeave).filter(
        DriverLeave.id == leave_id
    ).first()

    if not leave:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Leave not found",
        )

    if leave.status != "pending":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only pending leaves can be approved",
        )

    leave.status = "granted"
    db.commit()
    db.refresh(leave)

    return {"message": "Leave approved"}


# =====================================================
# REJECT LEAVE
# =====================================================

@router.put("/{leave_id}/reject", response_model=MessageResponse)
def reject_leave(
    leave_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Reject a pending leave request."""
    check_admin(current_user)

    leave = db.query(DriverLeave).filter(
        DriverLeave.id == leave_id
    ).first()

    if not leave:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Leave not found",
        )

    if leave.status != "pending":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only pending leaves can be rejected",
        )

    leave.status = "rejected"
    db.commit()
    db.refresh(leave)

    return {"message": "Leave rejected"}