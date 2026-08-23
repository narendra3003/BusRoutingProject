"""Driver leave management

Endpoints
- POST   /driver/leave/apply      -> Apply for leave (driver only)
- GET    /driver/leave            -> List leaves for the current driver (admin may list all)
- GET    /driver/leave/{leave_id} -> Get a specific leave
- DELETE /driver/leave/{leave_id} -> Cancel/delete a leave (owner or admin)
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from datetime import date
from typing import List

from ..database import get_db
from ..models import DriverLeave, Driver, LeaveStatus
from ..utils import get_current_user
from ..schemas import DriverLeaveCreate, DriverLeaveResponse

router = APIRouter()


# =========================
# HELPER
# =========================
def format_leave(l):
    return {
        "leave_id": l.id,
        "driver_id": l.driver_id,
        "start_date": l.start_date,
        "end_date": l.end_date,
        "reason": l.reason,
        "status": l.status.value,
        "created_at": l.created_at
    }


# =========================
# APPLY LEAVE
# =========================
@router.post("/apply", response_model=DriverLeaveResponse, status_code=status.HTTP_201_CREATED)
def apply_leave(
    payload: DriverLeaveCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Driver applies for leave
    """

    if current_user["role"] != "driver":
        raise HTTPException(status_code=403, detail="Only drivers allowed")

    driver_id = current_user["user_id"]

    # validate driver exists
    driver = db.query(Driver).filter(Driver.user_id == driver_id).first()
    if not driver:
        raise HTTPException(status_code=404, detail="Driver not found")

    start_date = payload.start_date
    end_date = payload.end_date
    reason = payload.reason or ""

    if end_date < start_date:
        raise HTTPException(status_code=400, detail="Invalid date range")

    # 🚨 CHECK OVERLAPPING LEAVE
    overlap = db.query(DriverLeave).filter(
        DriverLeave.driver_id == driver_id,
        DriverLeave.status != LeaveStatus.rejected,
        DriverLeave.start_date <= end_date,
        DriverLeave.end_date >= start_date
    ).first()

    if overlap:
        raise HTTPException(status_code=400, detail="Overlapping leave exists")

    leave = DriverLeave(
        driver_id=driver_id,
        start_date=start_date,
        end_date=end_date,
        reason=reason,
        status=LeaveStatus.pending,
    )

    db.add(leave)
    db.commit()
    db.refresh(leave)

    return DriverLeaveResponse(
        id=leave.id,
        driver_id=leave.driver_id,
        start_date=leave.start_date,
        end_date=leave.end_date,
        reason=leave.reason,
        status=leave.status.value if hasattr(leave.status, "value") else leave.status,
        created_at=leave.created_at,
    )


# =========================
# GET MY LEAVES
# =========================
@router.get("/", response_model=List[DriverLeaveResponse])
def get_my_leaves(
    status: LeaveStatus | None = Query(None),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Driver sees own leaves
    Admin can pass driver_id to view others
    """

    if current_user["role"] == "driver":
        driver_id = current_user["user_id"]
    else:
        raise HTTPException(status_code=403, detail="Only drivers allowed")

    query = db.query(DriverLeave).filter(
        DriverLeave.driver_id == driver_id
    )

    if status:
        query = query.filter(DriverLeave.status == status)

    leaves = query.order_by(DriverLeave.created_at.desc()).all()

    return [
        DriverLeaveResponse(
            id=l.id,
            driver_id=l.driver_id,
            start_date=l.start_date,
            end_date=l.end_date,
            reason=l.reason,
            status=l.status.value if hasattr(l.status, "value") else l.status,
            created_at=l.created_at,
        )
        for l in leaves
    ]


# =========================
# GET SINGLE LEAVE
# =========================
@router.get("/{leave_id}", response_model=DriverLeaveResponse)
def get_leave(
    leave_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):

    leave = db.query(DriverLeave).filter(DriverLeave.id == leave_id).first()

    if not leave:
        raise HTTPException(status_code=404, detail="Leave not found")

    if current_user["role"] != "admin" and leave.driver_id != current_user["user_id"]:
        raise HTTPException(status_code=403, detail="Not authorized")

    return DriverLeaveResponse(
        id=leave.id,
        driver_id=leave.driver_id,
        start_date=leave.start_date,
        end_date=leave.end_date,
        reason=leave.reason,
        status=leave.status.value if hasattr(leave.status, "value") else leave.status,
        created_at=leave.created_at,
    )


# =========================
# CANCEL LEAVE
# =========================
@router.delete("/{leave_id}")
def cancel_leave(
    leave_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):

    leave = db.query(DriverLeave).filter(
        DriverLeave.id == leave_id
    ).first()

    if not leave:
        raise HTTPException(status_code=404, detail="Leave not found")

    if leave.driver_id != current_user["user_id"]:
        raise HTTPException(status_code=403, detail="Not your leave")

    if leave.status == LeaveStatus.granted:
        raise HTTPException(status_code=400, detail="Cannot cancel approved leave")

    db.delete(leave)
    db.commit()

    return {"status": "deleted", "leave_id": leave_id}


# =========================
# ADMIN: APPROVE / REJECT
# =========================
@router.put("/{leave_id}/status")
def update_leave_status(
    leave_id: int,
    status: LeaveStatus,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):

    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Only admin allowed")

    leave = db.query(DriverLeave).filter(
        DriverLeave.id == leave_id
    ).first()

    if not leave:
        raise HTTPException(status_code=404, detail="Leave not found")

    leave.status = status
    db.commit()
    return {"status": "updated", "leave_id": leave_id, "new_status": status.value}


# Summary of changes:
# - Request and response shapes now use `DriverLeaveCreate` and `DriverLeaveResponse` from `..schemas`.
# - Endpoints return typed Pydantic responses (list/get/apply) to expose a clear OpenAPI contract.