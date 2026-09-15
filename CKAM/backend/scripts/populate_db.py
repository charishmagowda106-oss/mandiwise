import pandas as pd
from app.database.session import SessionLocal, engine, Base
from app.models.models import Crop, Mandi, HistoricalPrice
import app.models.models
import os
from pathlib import Path
from datetime import datetime

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_PATH = PROJECT_ROOT / 'data' / 'sample' / 'historical_prices.csv'

Base.metadata.create_all(bind=engine)

def populate():
    db = SessionLocal()
    
    if db.query(Crop).count() > 0:
        print("Database already populated.")
        return
        
    df = pd.read_csv(DATA_PATH)
    
    crops = df['crop'].unique()
    mandis = df['mandi'].unique()
    
    crop_map = {}
    for c in crops:
        crop = Crop(name=c, category='Cereal')
        db.add(crop)
        db.commit()
        db.refresh(crop)
        crop_map[c] = crop.id
        
    mandi_map = {}
    for m in mandis:
        mandi = Mandi(name=m, state='State A', district='District A', lat=20.0 + (len(mandi_map)*0.1), lng=78.0 + (len(mandi_map)*0.1))
        db.add(mandi)
        db.commit()
        db.refresh(mandi)
        mandi_map[m] = mandi.id
        
    for _, row in df.iterrows():
        hp = HistoricalPrice(
            crop_id=crop_map[row['crop']],
            mandi_id=mandi_map[row['mandi']],
            date=datetime.strptime(row['date'].split(' ')[0], '%Y-%m-%d').date(),
            modal_price=row['modal_price'],
            min_price=row['modal_price'] * 0.9,
            max_price=row['modal_price'] * 1.1,
            unit='quintal'
        )
        db.add(hp)
        
    db.commit()
    db.close()
    print("Database populated.")

if __name__ == "__main__":
    populate()
