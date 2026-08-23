from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from typing import Optional, List

from ..database import get_db
from ..models import Notification, User, NotificationType
from .. import models
from ..schemas import NotificationCreate, NotificationResponse
from ..utils import get_current_user

router = APIRouter()


# =========================
# HELPER: FORMAT RESPONSE
# =========================
def format_notification(n: Notification):
    return {
        "id": n.id,
        "title": n.title,
        "message": n.message,
        "type": n.type.value if n.type else None,
        "is_read": n.is_read,
        "created_at": n.created_at
    }

@router.get("/", response_model=List[NotificationResponse], summary="List notifications for a user")
def list_notifications(user_id: Optional[int] = None, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    """Return notifications for the current user. Admins may pass `user_id` to list for another user."""

    if current_user.get("role") == "admin" and user_id is not None:
        target_user = user_id
    else:
        target_user = current_user["user_id"]

    notifications = (
        db.query(models.Notification)
        .filter(models.Notification.user_id == target_user)
        .order_by(models.Notification.created_at.desc())
        .all()
    )

    return [
        NotificationResponse(
            id=n.id,
            user_id=n.user_id,
            title=n.title,
            message=n.message,
            type=n.type.value if n.type is not None else None,
            is_read=n.is_read,
            created_at=n.created_at,
        )
        for n in notifications
    ]


@router.post("/", status_code=status.HTTP_201_CREATED, response_model=NotificationResponse, summary="Create notification")
def create_notification(payload: NotificationCreate, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    """Create a notification. Only admins may create notifications for other users."""

    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Only admins can create notifications")

    user = db.query(models.User).filter(models.User.id == payload.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Target user not found")

    n = models.Notification(
        user_id=payload.user_id,
        title=payload.title,
        message=payload.message,
    )

    if payload.type:
        n.type = payload.type

    db.add(n)
    db.commit()
    db.refresh(n)

    return NotificationResponse(
        id=n.id,
        user_id=n.user_id,
        title=n.title,
        message=n.message,
        type=n.type.value if hasattr(n.type, "value") else n.type,
        is_read=n.is_read,
        created_at=n.created_at,
    )


@router.put("/{notification_id}/read", response_model=NotificationResponse, summary="Mark notification as read")
def mark_notification_read(notification_id: int, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    """Mark a notification as read. Owner or admin may perform this action."""

    n = db.query(models.Notification).filter(models.Notification.id == notification_id).first()
    if not n:
        raise HTTPException(status_code=404, detail="Notification not found")

    if current_user.get("role") != "admin" and n.user_id != current_user["user_id"]:
        raise HTTPException(status_code=403, detail="Not authorized to modify this notification")

    n.is_read = True
    db.add(n)
    db.commit()
    db.refresh(n)

    return NotificationResponse(
        id=n.id,
        user_id=n.user_id,
        title=n.title,
        message=n.message,
        type=n.type.value if hasattr(n.type, "value") else n.type,
        is_read=n.is_read,
        created_at=n.created_at,
    )


# Summary of changes:
# - Implemented notification endpoints using shared Pydantic schemas `NotificationCreate` and `NotificationResponse` from `..schemas`.
# - Added response_model annotations so OpenAPI schema is consistent and explicit.