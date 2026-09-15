import os

def write_file(path, content):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content.strip() + '\n')

auth_py = """
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.models.models import User
from app.schemas import schemas
from app.core.security import get_password_hash, verify_password, create_access_token
from app.api.dependencies import get_current_user

router = APIRouter()

@router.post("/register", response_model=schemas.UserOut)
def register(user_in: schemas.UserCreate, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == user_in.email).first()
    if user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    hashed_password = get_password_hash(user_in.password)
    new_user = User(
        email=user_in.email,
        password_hash=hashed_password,
        name=user_in.name,
        location_lat=user_in.location_lat,
        location_lng=user_in.location_lng
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

@router.post("/login", response_model=schemas.Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == form_data.username).first()
    if not user or not verify_password(form_data.password, user.password_hash):
        raise HTTPException(status_code=400, detail="Incorrect email or password")
    
    access_token = create_access_token(data={"sub": user.email})
    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/me", response_model=schemas.UserOut)
def read_users_me(current_user: User = Depends(get_current_user)):
    return current_user
"""
write_file('backend/app/api/endpoints/auth.py', auth_py)

crops_py = """
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
"""
write_file('backend/app/api/endpoints/crops.py', crops_py)

mandis_py = """
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
"""
write_file('backend/app/api/endpoints/mandis.py', mandis_py)

write_file('backend/app/api/endpoints/__init__.py', "")
