from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List
from app.database.session import get_db
from app.models.models import Crop
from app.schemas import schemas

router = APIRouter()

@router.get("/", response_model=List[schemas.CropOut])
def get_crops(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return db.query(Crop).offset(skip).limit(limit).all()
