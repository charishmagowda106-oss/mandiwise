"""Generate the labelled sample price history for every crop x real mandi,
then train the price model.

The history is DEMO/SAMPLE data (documented as such in the UI) built on
realistic Karnataka wholesale price levels with monthly seasonality, a per
mandi/crop factor, and noise. Live current rates come from AGMARKNET.
"""

import zlib
from datetime import datetime

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import OneHotEncoder
import joblib
from pathlib import Path

from app.database.session import SessionLocal
from app.models.models import Crop, Mandi

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_PATH = PROJECT_ROOT / 'data' / 'sample' / 'historical_prices.csv'
MODELS_DIR = PROJECT_ROOT / 'models'

# Approximate real Indian wholesale levels, ₹/quintal
BASE_PRICES = {
    'Rice': 2600, 'Wheat': 2500, 'Cotton': 7200, 'Maize': 2100, 'Soybean': 4600,
    'Paddy(Dhan)': 2300, 'Jowar(Sorghum)': 3400, 'Bajra(Pearl Millet)': 2600,
    'Ragi': 3300, 'Barley': 2700, 'Arhar (Tur/Red Gram)': 9800,
    'Bengal Gram(Gram)': 5900, 'Black Gram(Urd Beans)': 6600, 'Green Gram(Moong)': 7600,
    'Horse Gram': 5000, 'Cowpea(Veg)': 6800, 'Groundnut': 6900, 'Soyabean': 4600,
    'Sunflower': 6300, 'Sesamum(Sesame,Gingelly,Til)': 7800, 'Castor Seed': 5900,
    'Niger Seed': 9200, 'Onion': 1900, 'Tomato': 2600, 'Potato': 1700, 'Brinjal': 2700,
    'Bhindi(Ladies Finger)': 3100, 'Cabbage': 1600, 'Cauliflower': 1900, 'Carrot': 3100,
    'Chilli Green': 8800, 'Cucumber': 1900, 'Beans': 3600, 'Bitter gourd': 3600,
    'Raddish': 1700, 'Banana': 2700, 'Mango': 3600, 'Papaya': 2300,
    'Pomegranate': 6700, 'Grapes': 5600, 'Arecanut(Betelnut/Supari)': 22000,
    'Coconut': 11000, 'Dry Chillies': 15000, 'Turmeric': 8800, 'Coriander(Leaves)': 2600,
}
DEFAULT_BASE = 3000

YEARS = (2022, 2023)


def _load_catalogue():
    db = SessionLocal()
    try:
        crops = [name for (_id, name) in db.query(Crop.id, Crop.name).order_by(Crop.id).all()]
        mandis = [name for (_id, name) in db.query(Mandi.id, Mandi.name).order_by(Mandi.id).all()]
    finally:
        db.close()
    if not crops or not mandis:
        raise SystemExit("Crops/mandis are empty — seed the database first.")
    return crops, mandis


def generate_sample_data():
    """Write data/sample/historical_prices.csv for every crop x real mandi."""
    crops, mandis = _load_catalogue()
    dates = [datetime(year, month, 15) for year in YEARS for month in range(1, 13)]

    records = []
    for crop in crops:
        base = BASE_PRICES.get(crop, DEFAULT_BASE)
        crop_seed = zlib.crc32(crop.encode('utf-8'))
        for mandi in mandis:
            seed = (crop_seed + zlib.crc32(mandi.encode('utf-8'))) % (2 ** 32)
            rng = np.random.default_rng(seed)
            mandi_factor = 1.0 + rng.uniform(-0.06, 0.06)  # each market runs a bit rich/poor
            for date in dates:
                season_mult = 1.0 + 0.2 * np.sin(2 * np.pi * date.month / 12.0)
                noise = rng.normal(0, base * 0.025)
                modal_price = max(100.0, base * season_mult * mandi_factor + noise)
                records.append({
                    'date': date.strftime('%Y-%m-%d'),
                    'crop': crop,
                    'mandi': mandi,
                    'month': date.month,
                    'day': date.day,
                    'year': date.year,
                    'modal_price': round(modal_price, 2),
                })

    df = pd.DataFrame(records).sort_values(by=['date', 'crop', 'mandi'])
    df['lag_7_price'] = df.groupby(['crop', 'mandi'])['modal_price'].shift(1)
    df['lag_7_price'] = df.groupby(['crop', 'mandi'])['lag_7_price'].bfill()

    DATA_PATH.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(DATA_PATH, index=False)
    print(f"Wrote {len(df)} sample rows for {len(crops)} crops x {len(mandis)} real mandis -> {DATA_PATH}")
    return df


def train_model():
    df = pd.read_csv(DATA_PATH)

    features = ['month', 'day', 'year', 'lag_7_price']
    X_num = df[features]

    encoder = OneHotEncoder(sparse_output=False, handle_unknown='ignore')
    X_cat = encoder.fit_transform(df[['crop', 'mandi']])

    X = np.hstack([X_num, X_cat])
    y = df['modal_price']

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    model = RandomForestRegressor(n_estimators=40, max_depth=18, random_state=42, n_jobs=-1)
    model.fit(X_train, y_train)

    score = model.score(X_test, y_test)
    print(f"Model R2 Score: {score}")

    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, MODELS_DIR / 'price_model.joblib')
    joblib.dump(encoder, MODELS_DIR / 'encoder.joblib')
    print("Model and encoder saved to models/")


if __name__ == "__main__":
    generate_sample_data()
    train_model()
