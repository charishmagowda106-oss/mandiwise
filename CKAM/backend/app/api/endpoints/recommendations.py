from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.services.ranking import haversine, rank_mandis  # noqa: F401  (haversine re-exported)
from pydantic import BaseModel
from typing import List

router = APIRouter()

class CompareRequest(BaseModel):
    crop_id: int
    quantity: float
    unit: str = "quintal" # kg or quintal
    lat: float
    lng: float
    transport_rate_per_km: float = 10.0

class MandiRank(BaseModel):
    mandi_id: int
    mandi_name: str
    distance_km: float
    current_price: float
    transport_cost: float
    expected_revenue: float
    estimated_profit: float
    rank: int
    recommendation: str

@router.post("/compare", response_model=List[MandiRank])
def compare_mandis(req: CompareRequest, db: Session = Depends(get_db)):
    # Ranking lives in app.services.ranking so alerts use the exact same math.
    return rank_mandis(
        db,
        crop_id=req.crop_id,
        quantity=req.quantity,
        unit=req.unit,
        lat=req.lat,
        lng=req.lng,
        transport_rate_per_km=req.transport_rate_per_km,
    )
