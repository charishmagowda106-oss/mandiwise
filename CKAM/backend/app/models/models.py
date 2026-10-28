from sqlalchemy import Column, Integer, String, Float, Boolean, ForeignKey, Date, DateTime
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
    # Phone is optional at the DB level so pre-existing rows keep working;
    # the API requires it at sign-up. Used for OTP login and price alerts.
    phone = Column(String, unique=True, index=True, nullable=True)
    phone_verified = Column(Boolean, default=False)

    alerts = relationship("PriceAlert", back_populates="user", cascade="all, delete-orphan")
    notifications = relationship("Notification", back_populates="user", cascade="all, delete-orphan")

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

class OtpCode(Base):
    """One-shot login code sent to a phone (and mirrored to email when configured).

    Only a hash of the code is stored, so a leaked DB row cannot be replayed.
    """
    __tablename__ = "otp_codes"
    id = Column(Integer, primary_key=True, index=True)
    destination = Column(String, index=True, nullable=False)  # normalized phone, e.g. +919876543210
    code_hash = Column(String, nullable=False)
    purpose = Column(String, default="login")
    attempts = Column(Integer, default=0)
    expires_at = Column(DateTime, nullable=False)
    consumed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

class PriceAlert(Base):
    """Watch a crop for a profitable sale at the best mandi near the farmer."""
    __tablename__ = "price_alerts"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    crop_id = Column(Integer, ForeignKey("crops.id"), nullable=False)
    quantity = Column(Float, default=10.0)
    unit = Column(String, default="quintal")
    lat = Column(Float, nullable=True)
    lng = Column(Float, nullable=True)
    transport_rate_per_km = Column(Float, default=10.0)
    min_profit = Column(Float, nullable=True)      # notify when best profit reaches this (₹)
    active = Column(Boolean, default=True)
    # State of the last evaluation, so we only notify on meaningful change.
    last_best_mandi_id = Column(Integer, nullable=True)
    last_best_profit = Column(Float, nullable=True)
    last_notified_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="alerts")
    crop = relationship("Crop")

class Notification(Base):
    __tablename__ = "notifications"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    kind = Column(String, default="price_alert")   # price_alert | system
    title = Column(String, nullable=False)
    body = Column(String, nullable=False)
    link = Column(String, nullable=True)
    is_read = Column(Boolean, default=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    user = relationship("User", back_populates="notifications")
