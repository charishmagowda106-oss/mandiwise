import os

def write_file(path, content):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content.strip() + '\n')

session_py = """
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
import os

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./mandiwise.db")
connect_args = {"check_same_thread": False} if "sqlite" in DATABASE_URL else {}

engine = create_engine(DATABASE_URL, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
"""
write_file('backend/app/database/session.py', session_py)

models_py = """
from sqlalchemy import Column, Integer, String, Float, ForeignKey, Date, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database.session import Base

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    name = Column(String, nullable=False)
    location_lat = Column(Float, nullable=True)
    location_lng = Column(Float, nullable=True)
    language = Column(String, default="en")

class Crop(Base):
    __tablename__ = "crops"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True, nullable=False)
    category = Column(String, nullable=True)
    
class Mandi(Base):
    __tablename__ = "mandis"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True, nullable=False)
    state = Column(String, nullable=False)
    district = Column(String, nullable=False)
    lat = Column(Float, nullable=True)
    lng = Column(Float, nullable=True)

class HistoricalPrice(Base):
    __tablename__ = "historical_prices"
    id = Column(Integer, primary_key=True, index=True)
    crop_id = Column(Integer, ForeignKey("crops.id"), nullable=False)
    mandi_id = Column(Integer, ForeignKey("mandis.id"), nullable=False)
    date = Column(Date, nullable=False, index=True)
    min_price = Column(Float, nullable=True)
    max_price = Column(Float, nullable=True)
    modal_price = Column(Float, nullable=False)
    unit = Column(String, default="quintal")
    
    crop = relationship("Crop")
    mandi = relationship("Mandi")
"""
write_file('backend/app/models/models.py', models_py)

schemas_py = """
from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import date

class UserCreate(BaseModel):
    email: EmailStr
    password: str
    name: str
    location_lat: Optional[float] = None
    location_lng: Optional[float] = None

class UserOut(BaseModel):
    id: int
    email: str
    name: str
    location_lat: Optional[float]
    location_lng: Optional[float]
    
    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: Optional[str] = None

class CropOut(BaseModel):
    id: int
    name: str
    category: Optional[str]
    
    class Config:
        from_attributes = True

class MandiOut(BaseModel):
    id: int
    name: str
    state: str
    district: str
    lat: Optional[float]
    lng: Optional[float]
    
    class Config:
        from_attributes = True
        
class HistoricalPriceOut(BaseModel):
    id: int
    crop_id: int
    mandi_id: int
    date: date
    min_price: Optional[float]
    max_price: Optional[float]
    modal_price: float
    unit: str
    
    class Config:
        from_attributes = True
"""
write_file('backend/app/schemas/schemas.py', schemas_py)

security_py = """
from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
import os

SECRET_KEY = os.getenv("SECRET_KEY", "mandiwise_super_secret_key_change_me")
ALGORITHM = "HS256"

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(days=7)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt
"""
write_file('backend/app/core/security.py', security_py)

dependencies_py = """
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy.orm import Session
from app.core import security
from app.schemas import schemas
from app.database.session import get_db
from app.models.models import User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/auth/login")

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, security.SECRET_KEY, algorithms=[security.ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
        token_data = schemas.TokenData(email=email)
    except JWTError:
        raise credentials_exception
    user = db.query(User).filter(User.email == token_data.email).first()
    if user is None:
        raise credentials_exception
    return user
"""
write_file('backend/app/api/dependencies.py', dependencies_py)
