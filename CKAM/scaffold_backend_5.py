import os

def write_file(path, content):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content.strip() + '\n')

ml_predict_py = """
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.models.models import Crop, Mandi
from pydantic import BaseModel
import joblib
import numpy as np
from datetime import datetime, timedelta
import os

router = APIRouter()

model_path = os.path.join('models', 'price_model.joblib')
encoder_path = os.path.join('models', 'encoder.joblib')

class PredictRequest(BaseModel):
    crop_id: int
    mandi_id: int
    days_ahead: int = 7

class PredictResponse(BaseModel):
    current_price: float
    predicted_price: float
    expected_change_percent: float
    disclaimer: str = "Predictions are estimates based on historical market data and are not guaranteed market prices."

@router.post("/", response_model=PredictResponse)
def predict_price(req: PredictRequest, db: Session = Depends(get_db)):
    try:
        model = joblib.load(model_path)
        encoder = joblib.load(encoder_path)
    except FileNotFoundError:
        raise HTTPException(status_code=500, detail="ML model not found. Please train first.")
        
    crop = db.query(Crop).filter(Crop.id == req.crop_id).first()
    mandi = db.query(Mandi).filter(Mandi.id == req.mandi_id).first()
    
    if not crop or not mandi:
        raise HTTPException(status_code=404, detail="Crop or Mandi not found")
        
    # Mock finding current price
    current_price = 2500.0
    
    target_date = datetime.now() + timedelta(days=req.days_ahead)
    
    # feature arr: ['month', 'day', 'year', 'lag_7_price']
    X_num = np.array([[target_date.month, target_date.day, target_date.year, current_price]])
    X_cat = encoder.transform([[crop.name, mandi.name]])
    
    X = np.hstack([X_num, X_cat])
    pred = model.predict(X)[0]
    
    change = ((pred - current_price) / current_price) * 100
    
    return PredictResponse(
        current_price=current_price,
        predicted_price=round(pred, 2),
        expected_change_percent=round(change, 2)
    )
"""
write_file('backend/app/api/endpoints/ml_predict.py', ml_predict_py)

recommendations_py = """
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.models.models import Crop, Mandi
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
    a = math.sin(dLat/2) * math.sin(dLat/2) + math.cos(math.radians(lat1)) \
        * math.cos(math.radians(lat2)) * math.sin(dLon/2) * math.sin(dLon/2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    return R * c

@router.post("/compare", response_model=List[MandiRank])
def compare_mandis(req: CompareRequest, db: Session = Depends(get_db)):
    mandis = db.query(Mandi).all()
    
    quantity_quintals = req.quantity if req.unit == 'quintal' else req.quantity / 100.0
    
    results = []
    for m in mandis:
        if m.lat is None or m.lng is None:
            continue
        dist = haversine(req.lat, req.lng, m.lat, m.lng)
        
        # Mock price fetch
        price_per_quintal = 2500.0 + (m.id * 100)
        
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
"""
write_file('backend/app/api/endpoints/recommendations.py', recommendations_py)
