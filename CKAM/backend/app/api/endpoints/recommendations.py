from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.models.models import Crop, Mandi, HistoricalPrice
from pydantic import BaseModel
from typing import List
import math

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

def haversine(lat1, lon1, lat2, lon2):
    R = 6371 # km
    dLat = math.radians(lat2 - lat1)
    dLon = math.radians(lon2 - lon1)
    a = math.sin(dLat/2) * math.sin(dLat/2) + math.cos(math.radians(lat1))         * math.cos(math.radians(lat2)) * math.sin(dLon/2) * math.sin(dLon/2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    return R * c

@router.post("/compare", response_model=List[MandiRank])
def compare_mandis(req: CompareRequest, db: Session = Depends(get_db)):
    crop = db.query(Crop).filter(Crop.id == req.crop_id).first()
    if not crop:
        return []
    mandis = db.query(Mandi).all()
    
    quantity_quintals = req.quantity if req.unit == 'quintal' else req.quantity / 100.0
    
    results = []
    for m in mandis:
        if m.lat is None or m.lng is None:
            continue
        dist = haversine(req.lat, req.lng, m.lat, m.lng)
        
        latest_price = (
            db.query(HistoricalPrice)
            .filter(
                HistoricalPrice.crop_id == req.crop_id,
                HistoricalPrice.mandi_id == m.id,
            )
            .order_by(HistoricalPrice.date.desc())
            .first()
        )
        if not latest_price:
            continue
        price_per_quintal = latest_price.modal_price
        
        revenue = price_per_quintal * quantity_quintals
        transport = dist * req.transport_rate_per_km
        profit = revenue - transport
        
        results.append({
            "mandi_id": m.id,
            "mandi_name": m.name,
            "distance_km": round(dist, 2),
            "current_price": round(price_per_quintal, 2),
            "transport_cost": round(transport, 2),
            "expected_revenue": round(revenue, 2),
            "estimated_profit": round(profit, 2)
        })
        
    results.sort(key=lambda x: x["estimated_profit"], reverse=True)
    
    for idx, r in enumerate(results):
        r["rank"] = idx + 1
        if idx == 0:
            r["recommendation"] = "BEST MANDI"
        else:
            r["recommendation"] = "ALTERNATIVE"
            
    return results
