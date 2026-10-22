"""Historical price time-series for the trend charts."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.models.models import Crop, Mandi, HistoricalPrice

router = APIRouter()


@router.get("/history")
def price_history(crop_id: int, mandi_id: int, limit: int = 24, db: Session = Depends(get_db)):
    """Return the monthly price history for one crop at one mandi.

    The bundled sample history holds one row per month per crop x mandi, so the
    default limit of 24 gives a clean two-year trend line for the charts.
    Dates come back oldest -> newest so graphs draw left to right.
    """
    crop = db.query(Crop).filter(Crop.id == crop_id).first()
    if not crop:
        raise HTTPException(status_code=404, detail="Crop not found")
    mandi = db.query(Mandi).filter(Mandi.id == mandi_id).first()
    if not mandi:
        raise HTTPException(status_code=404, detail="Mandi not found")

    rows = (
        db.query(HistoricalPrice)
        .filter(HistoricalPrice.crop_id == crop_id, HistoricalPrice.mandi_id == mandi_id)
        .order_by(HistoricalPrice.date.desc())
        .limit(max(1, min(limit, 60)))
        .all()
    )
    rows.reverse()

    return {
        "crop": crop.name,
        "mandi": mandi.name,
        "unit": rows[0].unit if rows else "quintal",
        "points": [
            {
                "date": row.date.isoformat(),
                "min_price": row.min_price,
                "max_price": row.max_price,
                "modal_price": row.modal_price,
            }
            for row in rows
        ],
    }
