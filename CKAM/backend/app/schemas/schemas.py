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
