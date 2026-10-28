"""Price alerts: watch a crop and get a notification when selling it at the
best nearby mandi would earn at least the farmer's target profit."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.models.models import Crop, PriceAlert, User
from app.schemas import schemas
from app.api.dependencies import get_current_user

router = APIRouter()


def _serialize(alert: PriceAlert) -> schemas.PriceAlertOut:
    out = schemas.PriceAlertOut.model_validate(alert)
    out.crop_name = alert.crop.name if alert.crop else None
    return out


def _resolve_location(alert_in: schemas.PriceAlertCreate, user: User) -> tuple:
    lat = alert_in.lat if alert_in.lat is not None else user.location_lat
    lng = alert_in.lng if alert_in.lng is not None else user.location_lng
    if lat is None or lng is None:
        raise HTTPException(
            status_code=400,
            detail="Location needed for alerts — set it on your profile or allow it when creating the alert",
        )
    return lat, lng


@router.get("", response_model=list[schemas.PriceAlertOut])
def list_alerts(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    alerts = (
        db.query(PriceAlert)
        .filter(PriceAlert.user_id == current_user.id)
        .order_by(PriceAlert.created_at.desc())
        .all()
    )
    return [_serialize(alert) for alert in alerts]


@router.post("", response_model=schemas.PriceAlertOut, status_code=201)
def create_alert(
    alert_in: schemas.PriceAlertCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if db.query(Crop).filter(Crop.id == alert_in.crop_id).first() is None:
        raise HTTPException(status_code=404, detail="Unknown crop")
    lat, lng = _resolve_location(alert_in, current_user)
    alert = PriceAlert(
        user_id=current_user.id,
        crop_id=alert_in.crop_id,
        quantity=alert_in.quantity,
        unit=alert_in.unit,
        lat=lat,
        lng=lng,
        transport_rate_per_km=alert_in.transport_rate_per_km,
        min_profit=alert_in.min_profit,
    )
    db.add(alert)
    db.commit()
    db.refresh(alert)
    return _serialize(alert)


def _get_owned_alert(alert_id: int, current_user: User, db: Session) -> PriceAlert:
    alert = db.get(PriceAlert, alert_id)
    if alert is None or alert.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Alert not found")
    return alert


@router.patch("/{alert_id}", response_model=schemas.PriceAlertOut)
def update_alert(
    alert_id: int,
    patch: schemas.PriceAlertUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    alert = _get_owned_alert(alert_id, current_user, db)
    data = patch.model_dump(exclude_unset=True)
    if "min_profit" in data and data["min_profit"] is None:
        # PATCH {"min_profit": null} clears the target (notify on any improvement).
        alert.min_profit = None
        data.pop("min_profit")
    for key, value in data.items():
        setattr(alert, key, value)
    db.commit()
    db.refresh(alert)
    return _serialize(alert)


@router.delete("/{alert_id}", status_code=204)
def delete_alert(
    alert_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    alert = _get_owned_alert(alert_id, current_user, db)
    db.delete(alert)
    db.commit()


@router.post("/{alert_id}/check")
def check_alert_now(
    alert_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Evaluate one alert immediately (also what the background worker runs)."""
    from app.services.alert_checker import evaluate_alert

    alert = _get_owned_alert(alert_id, current_user, db)
    notification = evaluate_alert(db, alert)
    db.refresh(alert)
    return {
        "notified": notification is not None,
        "notification": notification.title if notification else None,
        "last_best_profit": alert.last_best_profit,
        "last_best_mandi_id": alert.last_best_mandi_id,
        "min_profit": alert.min_profit,
    }
