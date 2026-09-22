from pydantic import BaseModel, EmailStr, Field, field_validator
from typing import Optional, List
from datetime import date

class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=72)
    name: str = Field(min_length=2, max_length=100)
    location_lat: Optional[float] = None
    location_lng: Optional[float] = None

    @field_validator("password")
    @classmethod
    def password_fits_bcrypt(cls, value: str) -> str:
        if len(value.encode("utf-8")) > 72:
            raise ValueError("Password must be at most 72 bytes")
        return value

class UserOut(BaseModel):
    id: int
    email: str
    name: str
    location_lat: Optional[float]
    location_lng: Optional[float]
    
    class Config:
        from_attributes = True

class UserUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=2, max_length=100)
    location_lat: Optional[float] = None
    location_lng: Optional[float] = None

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
