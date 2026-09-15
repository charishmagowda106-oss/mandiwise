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
