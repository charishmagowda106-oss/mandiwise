from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List
from app.database.session import get_db
from app.models.models import Crop
from app.schemas import schemas

router = APIRouter()

# Common Karnataka food grains, pulses, oilseeds, spices, fruits and vegetables.
# This catalogue is independent of a transient day's live feed, so a crop stays
# selectable even when no market reported it that day.
KARNATAKA_CROPS = {
    "Cereals": ["Paddy(Dhan)", "Maize", "Jowar(Sorghum)", "Bajra(Pearl Millet)", "Ragi", "Wheat", "Barley"],
    "Pulses": ["Arhar (Tur/Red Gram)", "Bengal Gram(Gram)", "Black Gram(Urd Beans)", "Green Gram(Moong)", "Horse Gram", "Cowpea(Veg)"],
    "Oilseeds": ["Groundnut", "Soyabean", "Sunflower", "Sesamum(Sesame,Gingelly,Til)", "Castor Seed", "Niger Seed"],
    "Vegetables": ["Onion", "Tomato", "Potato", "Brinjal", "Bhindi(Ladies Finger)", "Cabbage", "Cauliflower", "Carrot", "Chilli Green", "Cucumber", "Beans", "Bitter gourd", "Raddish"],
    "Fruits & spices": ["Banana", "Mango", "Papaya", "Pomegranate", "Grapes", "Arecanut(Betelnut/Supari)", "Coconut", "Dry Chillies", "Turmeric", "Coriander(Leaves)"]
}


def ensure_karnataka_crops(db: Session) -> None:
    existing = {name for (name,) in db.query(Crop.name).all()}
    additions = [Crop(name=name, category=category) for category, names in KARNATAKA_CROPS.items() for name in names if name not in existing]
    if additions:
        db.add_all(additions)
        db.commit()

@router.get("/", response_model=List[schemas.CropOut])
def get_crops(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    ensure_karnataka_crops(db)
    return db.query(Crop).order_by(Crop.category, Crop.name).offset(skip).limit(limit).all()
