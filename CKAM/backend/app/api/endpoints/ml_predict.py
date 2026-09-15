from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.models.models import Crop, Mandi, HistoricalPrice
from pydantic import BaseModel
import joblib
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from pathlib import Path

router = APIRouter()

PROJECT_ROOT = Path(__file__).resolve().parents[4]
model_path = PROJECT_ROOT / 'models' / 'price_model.joblib'
encoder_path = PROJECT_ROOT / 'models' / 'encoder.joblib'

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
        
    latest_price = (
        db.query(HistoricalPrice)
        .filter(
            HistoricalPrice.crop_id == req.crop_id,
            HistoricalPrice.mandi_id == req.mandi_id,
        )
        .order_by(HistoricalPrice.date.desc())
        .first()
    )
    if not latest_price:
        raise HTTPException(status_code=404, detail="No historical price found for this crop and mandi")
    current_price = latest_price.modal_price
    
    target_date = datetime.now() + timedelta(days=req.days_ahead)
    
    # feature arr: ['month', 'day', 'year', 'lag_7_price']
    X_num = np.array([[target_date.month, target_date.day, target_date.year, current_price]])
    X_cat = encoder.transform(pd.DataFrame([[crop.name, mandi.name]], columns=['crop', 'mandi']))
    
    X = np.hstack([X_num, X_cat])
    pred = model.predict(X)[0]
    
    change = ((pred - current_price) / current_price) * 100
    
    return PredictResponse(
        current_price=current_price,
        predicted_price=round(pred, 2),
        expected_change_percent=round(change, 2)
    )
