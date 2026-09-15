import os

def write_file(path, content):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content.strip() + '\n')

train_ml_py = """
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import OneHotEncoder
import joblib
import os
from datetime import datetime, timedelta

def generate_sample_data():
    np.random.seed(42)
    crops = ['Wheat', 'Rice', 'Maize', 'Cotton', 'Soybean']
    mandis = ['Mandi A', 'Mandi B', 'Mandi C', 'Mandi D']
    
    data = []
    start_date = datetime(2021, 1, 1)
    for i in range(1000):
        crop = np.random.choice(crops)
        mandi = np.random.choice(mandis)
        date = start_date + timedelta(days=np.random.randint(0, 1000))
        
        # Base price
        base = {'Wheat': 2000, 'Rice': 3000, 'Maize': 1800, 'Cotton': 6000, 'Soybean': 4000}[crop]
        # Seasonality (month)
        month = date.month
        season_mult = 1.0 + 0.2 * np.sin(2 * np.pi * month / 12.0)
        # Random noise
        noise = np.random.normal(0, 100)
        
        modal_price = base * season_mult + noise
        
        data.append({
            'date': date,
            'crop': crop,
            'mandi': mandi,
            'month': month,
            'day': date.day,
            'year': date.year,
            'modal_price': round(modal_price, 2)
        })
        
    df = pd.DataFrame(data)
    df = df.sort_values(by='date')
    
    # Lag feature
    df['lag_7_price'] = df.groupby(['crop', 'mandi'])['modal_price'].shift(1)
    df.fillna(method='bfill', inplace=True)
    
    os.makedirs('data/sample', exist_ok=True)
    df.to_csv('data/sample/historical_prices.csv', index=False)
    return df

def train_model():
    df = generate_sample_data()
    
    features = ['month', 'day', 'year', 'lag_7_price']
    X_num = df[features]
    
    encoder = OneHotEncoder(sparse_output=False, handle_unknown='ignore')
    X_cat = encoder.fit_transform(df[['crop', 'mandi']])
    
    X = np.hstack([X_num, X_cat])
    y = df['modal_price']
    
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    model = RandomForestRegressor(n_estimators=50, random_state=42)
    model.fit(X_train, y_train)
    
    score = model.score(X_test, y_test)
    print(f"Model R2 Score: {score}")
    
    os.makedirs('models', exist_ok=True)
    joblib.dump(model, 'models/price_model.joblib')
    joblib.dump(encoder, 'models/encoder.joblib')
    print("Model and encoder saved to models/")

if __name__ == "__main__":
    train_model()
"""
write_file('backend/scripts/train_ml.py', train_ml_py)

populate_db_py = """
import pandas as pd
from app.database.session import SessionLocal, engine, Base
from app.models.models import Crop, Mandi, HistoricalPrice
import app.models.models
import os
from datetime import datetime

Base.metadata.create_all(bind=engine)

def populate():
    db = SessionLocal()
    
    if db.query(Crop).count() > 0:
        print("Database already populated.")
        return
        
    df = pd.read_csv('data/sample/historical_prices.csv')
    
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
"""
write_file('backend/scripts/populate_db.py', populate_db_py)
