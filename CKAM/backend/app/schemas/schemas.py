from pydantic import BaseModel, EmailStr, Field, field_validator
from typing import Optional, List
from datetime import date, datetime

from app.core.phone import InvalidPhone, normalize_phone

class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=72)
    name: str = Field(min_length=2, max_length=100)
    phone: str = Field(min_length=6, max_length=20, description="10-digit Indian mobile number")
    location_lat: Optional[float] = None
    location_lng: Optional[float] = None

    @field_validator("phone")
    @classmethod
    def phone_is_valid(cls, value: str) -> str:
        try:
            return normalize_phone(value)
        except InvalidPhone as exc:
            raise ValueError(str(exc))

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
    phone: Optional[str] = None
    phone_verified: bool = False
    language: str = "en"
    
    class Config:
        from_attributes = True

class UserUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=2, max_length=100)
    location_lat: Optional[float] = None
    location_lng: Optional[float] = None

    class Config:
        from_attributes = True

class OtpRequest(BaseModel):
    phone: str = Field(min_length=6, max_length=20)

    @field_validator("phone")
    @classmethod
    def phone_is_valid(cls, value: str) -> str:
        try:
            return normalize_phone(value)
        except InvalidPhone as exc:
            raise ValueError(str(exc))

class OtpVerify(BaseModel):
    phone: str = Field(min_length=6, max_length=20)
    code: str = Field(min_length=6, max_length=6)

    @field_validator("phone")
    @classmethod
    def phone_is_valid(cls, value: str) -> str:
        try:
            return normalize_phone(value)
        except InvalidPhone as exc:
            raise ValueError(str(exc))

class OtpSent(BaseModel):
    message: str
    masked_phone: str
    expires_in: int
    resend_after: int
    dev_code: Optional[str] = None  # only present in dev mode (no SMS/email channel)

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

class PriceAlertCreate(BaseModel):
    crop_id: int
    quantity: float = Field(gt=0, le=100000)
    unit: str = "quintal"
    lat: Optional[float] = None
    lng: Optional[float] = None
    transport_rate_per_km: float = Field(default=10.0, ge=0, le=1000)
    min_profit: Optional[float] = Field(default=None, description="Notify when best estimated profit reaches this (INR)")

class PriceAlertUpdate(BaseModel):
    active: Optional[bool] = None
    min_profit: Optional[float] = Field(default=None, ge=0)
    quantity: Optional[float] = Field(default=None, gt=0, le=100000)

class PriceAlertOut(BaseModel):
    id: int
    crop_id: int
    crop_name: Optional[str] = None
    quantity: float
    unit: str
    lat: Optional[float]
    lng: Optional[float]
    transport_rate_per_km: float
    min_profit: Optional[float]
    active: bool
    last_best_mandi_id: Optional[int]
    last_best_profit: Optional[float]
    last_notified_at: Optional[datetime]
    created_at: datetime

    class Config:
        from_attributes = True

class NotificationOut(BaseModel):
    id: int
    kind: str
    title: str
    body: str
    link: Optional[str]
    is_read: bool
    created_at: datetime

    class Config:
        from_attributes = True

class NotificationPage(BaseModel):
    items: List[NotificationOut]
    unread: int
