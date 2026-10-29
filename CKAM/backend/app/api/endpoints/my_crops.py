"""My Crops: the farmer's personal ledger of sown crops.

Each entry is enriched on read with the live best mandi for that crop
(reusing the shared ranking service), a harvest countdown, and a simple
status the dashboard turns into a colored pill:
  watching (no harvest date) | growing | soon (<= 14 days) | ready (due/past)
"""
from __future__ import annotations

from datetime import date

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user
from app.database.session import get_db
from app.models.models import Crop, User, UserCrop
from app.schemas import schemas
from app.services.ranking import rank_mandis

router = APIRouter()

MAX_CROPS_PER_USER = 30
SOON_DAYS = 14
TRANSPORT_RATE_PER_KM = 10.0


def _status(days_to_harvest) -> str:
    if days_to_harvest is None:
        return "watching"
    if days_to_harvest < 0:
        return "ready"
    if days_to_harvest == 0:
        return "ready"
    if days_to_harvest <= SOON_DAYS:
        return "soon"
    return "growing"


def _best_now(db: Session, uc: UserCrop, user: User) -> schemas.BestNow | None:
    lat = uc.lat if uc.lat is not None else user.location_lat
    lng = uc.lng if uc.lng is not None else user.location_lng
    if lat is None or lng is None:
        return None
    ranking = rank_mandis(
        db,
        crop_id=uc.crop_id,
        quantity=uc.quantity,
        unit="quintal",
        lat=lat,
        lng=lng,
        transport_rate_per_km=TRANSPORT_RATE_PER_KM,
    )
    if not ranking:
        return None
    best = ranking[0]
    return schemas.BestNow(
        mandi_name=best["mandi_name"],
        distance_km=best["distance_km"],
        current_price=best["current_price"],
        expected_revenue=best["expected_revenue"],
        estimated_profit=best["estimated_profit"],
    )


def _serialize(db: Session, uc: UserCrop, user: User) -> schemas.UserCropOut:
    days = (uc.expected_harvest_date - date.today()).days if uc.expected_harvest_date else None
    costs = [uc.cost_seed, uc.cost_fertilizer, uc.cost_labor, uc.cost_other]
    total_cost = sum(c for c in costs if c is not None) if any(c is not None for c in costs) else None
    out = schemas.UserCropOut(
        id=uc.id,
        crop_id=uc.crop_id,
        crop_name=uc.crop.name if uc.crop else "Crop",
        category=uc.crop.category if uc.crop else None,
        quantity=uc.quantity,
        sown_date=uc.sown_date,
        expected_harvest_date=uc.expected_harvest_date,
        days_to_harvest=days,
        status=_status(days),
        total_cost=total_cost,
        cost_seed=uc.cost_seed,
        cost_fertilizer=uc.cost_fertilizer,
        cost_labor=uc.cost_labor,
        cost_other=uc.cost_other,
        best=_best_now(db, uc, user),
        created_at=uc.created_at,
    )
    return out


@router.get("", response_model=list[schemas.UserCropOut])
def list_my_crops(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    crops = (
        db.query(UserCrop)
        .filter(UserCrop.user_id == current_user.id)
        .order_by(UserCrop.created_at.desc())
        .all()
    )
    return [_serialize(db, uc, current_user) for uc in crops]


@router.post("", response_model=schemas.UserCropOut, status_code=201)
def add_my_crop(
    crop_in: schemas.UserCropCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if db.query(Crop).filter(Crop.id == crop_in.crop_id).first() is None:
        raise HTTPException(status_code=404, detail="Unknown crop")
    count = db.query(UserCrop).filter(UserCrop.user_id == current_user.id).count()
    if count >= MAX_CROPS_PER_USER:
        raise HTTPException(status_code=400, detail=f"Limit of {MAX_CROPS_PER_USER} crops reached")
    uc = UserCrop(user_id=current_user.id, **crop_in.model_dump())
    db.add(uc)
    db.commit()
    db.refresh(uc)
    return _serialize(db, uc, current_user)


def _get_owned(crop_row_id: int, current_user: User, db: Session) -> UserCrop:
    uc = db.get(UserCrop, crop_row_id)
    if uc is None or uc.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Crop not found")
    return uc


@router.patch("/{crop_row_id}", response_model=schemas.UserCropOut)
def update_my_crop(
    crop_row_id: int,
    patch: schemas.UserCropUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    uc = _get_owned(crop_row_id, current_user, db)
    data = patch.model_dump(exclude_unset=True)
    # Moving the harvest date re-arms the harvest notification.
    if "expected_harvest_date" in data and data["expected_harvest_date"] != uc.expected_harvest_date:
        uc.harvest_notified_at = None
    for key, value in data.items():
        setattr(uc, key, value)
    db.commit()
    db.refresh(uc)
    return _serialize(db, uc, current_user)


@router.delete("/{crop_row_id}", status_code=204)
def delete_my_crop(
    crop_row_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    uc = _get_owned(crop_row_id, current_user, db)
    db.delete(uc)
    db.commit()
