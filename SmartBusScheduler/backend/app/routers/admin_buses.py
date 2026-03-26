from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Bus, BusStatus
from ..utils import get_current_user
from ..schemas import BusCreate, BusResponse

router = APIRouter()


def ensure_admin(current_user: dict):
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin only")


@router.post("/", response_model=BusResponse, status_code=status.HTTP_201_CREATED)
def create_bus(payload: BusCreate, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    ensure_admin(current_user)

    existing = db.query(Bus).filter(Bus.code == payload.code).first()
    if existing:
        raise HTTPException(status_code=400, detail="Bus code already exists")

    bus = Bus(
        code=payload.code,
        sitting_capacity=payload.sitting_capacity,
        standing_capacity=payload.standing_capacity,
        status=payload.status if payload.status else BusStatus.active,
    )

    db.add(bus)
    db.commit()
    db.refresh(bus)

    return BusResponse(
        id=bus.id,
        code=bus.code,
        sitting_capacity=bus.sitting_capacity,
        standing_capacity=bus.standing_capacity,
        status=bus.status.value if hasattr(bus.status, "value") else bus.status,
        created_at=bus.created_at,
    )


@router.get("/", response_model=List[BusResponse])
def get_buses(status: Optional[BusStatus] = Query(None), db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    ensure_admin(current_user)

    q = db.query(Bus)
    if status:
        q = q.filter(Bus.status == status)

    buses = q.order_by(Bus.id).all()
    return [
        BusResponse(
            id=b.id,
            code=b.code,
            sitting_capacity=b.sitting_capacity,
            standing_capacity=b.standing_capacity,
            status=b.status.value if hasattr(b.status, "value") else b.status,
            created_at=b.created_at,
        )
        for b in buses
    ]


@router.get("/{bus_id}", response_model=BusResponse)
def get_bus(bus_id: int, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    ensure_admin(current_user)
    bus = db.query(Bus).filter(Bus.id == bus_id).first()
    if not bus:
        raise HTTPException(status_code=404, detail="Bus not found")

    return BusResponse(
        id=bus.id,
        code=bus.code,
        sitting_capacity=bus.sitting_capacity,
        standing_capacity=bus.standing_capacity,
        status=bus.status.value if hasattr(bus.status, "value") else bus.status,
        created_at=bus.created_at,
    )


@router.put("/{bus_id}", response_model=BusResponse)
def update_bus(bus_id: int, payload: BusCreate, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    ensure_admin(current_user)

    bus = db.query(Bus).filter(Bus.id == bus_id).first()
    if not bus:
        raise HTTPException(status_code=404, detail="Bus not found")

    # apply updates
    if payload.code:
        existing = db.query(Bus).filter(Bus.code == payload.code, Bus.id != bus_id).first()
        if existing:
            raise HTTPException(status_code=400, detail="Bus code already exists")
        bus.code = payload.code

    bus.sitting_capacity = payload.sitting_capacity
    bus.standing_capacity = payload.standing_capacity
    if payload.status:
        bus.status = payload.status

    db.add(bus)
    db.commit()
    db.refresh(bus)

    return BusResponse(
        id=bus.id,
        code=bus.code,
        sitting_capacity=bus.sitting_capacity,
        standing_capacity=bus.standing_capacity,
        status=bus.status.value if hasattr(bus.status, "value") else bus.status,
        created_at=bus.created_at,
    )


@router.delete("/{bus_id}")
def delete_bus(bus_id: int, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    ensure_admin(current_user)

    bus = db.query(Bus).filter(Bus.id == bus_id).first()
    if not bus:
        raise HTTPException(status_code=404, detail="Bus not found")

    bus.status = BusStatus.inactive
    db.commit()

    return {"status": "deleted", "bus_id": bus_id}


# Summary:
# - Converted admin buses endpoints to use `BusCreate` and `BusResponse` schemas and response_model annotations.