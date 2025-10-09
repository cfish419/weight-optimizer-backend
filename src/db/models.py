from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from .database import Base


class Flight(Base):
    __tablename__ = "flights"

    id = Column(String, primary_key=True)
    flight_number = Column(String, index=True)
    departure = Column(String)
    arrival = Column(String)
    aircraft_type = Column(String)
    departure_time = Column(DateTime)
    estimated_passengers = Column(Integer)

    # Relationship with baggage
    baggage_items = relationship("Baggage", back_populates="flight")


class Baggage(Base):
    __tablename__ = "baggage"

    id = Column(String, primary_key=True)
    tag_number = Column(String, unique=True, index=True)
    weight_kg = Column(Float)
    length_cm = Column(Float)
    width_cm = Column(Float)
    height_cm = Column(Float)
    passenger_name = Column(String)
    priority = Column(String)
    category = Column(String)
    status = Column(String)

    # Foreign key to flight
    flight_id = Column(String, ForeignKey("flights.id"))
    flight = relationship("Flight", back_populates="baggage_items")
