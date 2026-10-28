"""In-app notifications (the bell icon): price alerts and system messages."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.models.models import Notification, User
from app.schemas import schemas
from app.api.dependencies import get_current_user

router = APIRouter()


@router.get("", response_model=schemas.NotificationPage)
def list_notifications(
    limit: int = 20,
    unread_only: bool = False,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    query = db.query(Notification).filter(Notification.user_id == current_user.id)
    unread = query.filter(Notification.is_read.is_(False)).count()
    if unread_only:
        query = query.filter(Notification.is_read.is_(False))
    items = query.order_by(Notification.created_at.desc()).limit(max(1, min(limit, 100))).all()
    return {"items": items, "unread": unread}


@router.post("/{notification_id}/read", response_model=schemas.NotificationOut)
def mark_read(
    notification_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    item = db.get(Notification, notification_id)
    if item is None or item.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Notification not found")
    item.is_read = True
    db.commit()
    db.refresh(item)
    return item


@router.post("/read-all")
def mark_all_read(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    db.query(Notification).filter(
        Notification.user_id == current_user.id, Notification.is_read.is_(False)
    ).update({"is_read": True}, synchronize_session=False)
    db.commit()
    return {"status": "ok"}
