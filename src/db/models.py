from sqlalchemy import Column, String, Float, DateTime, Integer, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import relationship
from datetime import datetime
import enum
from .database import Base
import uuid

class LabelColor(enum.Enum):
    RED = "red"
    YELLOW = "yellow"
    BLUE = "blue"

class Aircraft(Base):
    __tablename__ = "aircraft"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    model = Column(String, nullable=False)
    max_cargo_weight = Column(Float, nullable=False)
    max_cargo_volume = Column(Float, nullable=False)
    length = Column(Float, nullable=False)  # Aircraft cargo hold length in meters
    width = Column(Float, nullable=False)   # Aircraft cargo hold width in meters
    height = Column(Float, nullable=False)  # Aircraft cargo hold height in meters
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    flights = relationship("Flight", back_populates="aircraft")

class Flight(Base):
    __tablename__ = "flights"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    flight_number = Column(String, nullable=False)
    aircraft_id = Column(String, ForeignKey("aircraft.id"), nullable=False)
    departure_time = Column(DateTime, nullable=False)
    arrival_time = Column(DateTime, nullable=False)
    status = Column(String, default="scheduled")
    current_weight = Column(Float, default=0)
    current_volume = Column(Float, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    aircraft = relationship("Aircraft", back_populates="flights")
    baggage_items = relationship("Baggage", back_populates="flight")
    loading_plan = relationship("LoadingPlan", back_populates="flight", uselist=False)

class Baggage(Base):
    __tablename__ = "baggage"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    flight_id = Column(String, ForeignKey("flights.id"), nullable=False)
    mass = Column(Float, nullable=False)
    volume = Column(Float, nullable=False)
    density = Column(Float, nullable=False)
    image_url = Column(String, nullable=True)
    label_color = Column(SQLEnum(LabelColor), nullable=True)
    loading_order = Column(Integer, nullable=True)
    position_x = Column(Float, nullable=True)  # X coordinate in cargo hold
    position_y = Column(Float, nullable=True)  # Y coordinate in cargo hold
    position_z = Column(Float, nullable=True)  # Z coordinate in cargo hold
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    flight = relationship("Flight", back_populates="baggage_items")

class LoadingPlan(Base):
    __tablename__ = "loading_plans"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    flight_id = Column(String, ForeignKey("flights.id"), unique=True)
    total_weight = Column(Float, nullable=False)
    total_volume = Column(Float, nullable=False)
    center_of_gravity_x = Column(Float, nullable=False)
    center_of_gravity_y = Column(Float, nullable=False)
    center_of_gravity_z = Column(Float, nullable=False)
    fuel_efficiency_gain = Column(Float)  # Estimated fuel savings in percentage
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    flight = relationship("Flight", back_populates="loading_plan")