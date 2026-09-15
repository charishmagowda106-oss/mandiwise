import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import OneHotEncoder
import joblib
import os
from pathlib import Path
from datetime import datetime, timedelta

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_PATH = PROJECT_ROOT / 'data' / 'sample' / 'historical_prices.csv'
MODELS_DIR = PROJECT_ROOT / 'models'

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
    
    DATA_PATH.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(DATA_PATH, index=False)
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
    
    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, MODELS_DIR / 'price_model.joblib')
    joblib.dump(encoder, MODELS_DIR / 'encoder.joblib')
    print("Model and encoder saved to models/")

if __name__ == "__main__":
    train_model()
