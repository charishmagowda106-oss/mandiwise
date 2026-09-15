from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List
from app.database.session import get_db
from app.models.models import Mandi
from app.schemas import schemas

router = APIRouter()

@router.get("/", response_model=List[schemas.MandiOut])
def get_mandis(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return db.query(Mandi).offset(skip).limit(limit).all()
