"""
Schemas for real-time vehicle location tracking
"""
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from uuid import UUID


class VehicleLocationUpdate(BaseModel):
    """Schema for updating vehicle position"""
    vehicle_id: UUID
    booking_id: Optional[UUID] = None
    lat: float
    lng: float
    speed: Optional[float] = None  # km/h
    heading: Optional[float] = None  # degrees
    accuracy: Optional[float] = None  # meters


class VehicleLocationResponse(BaseModel):
    """Schema for returning location data"""
    vehicle_id: str
    booking_id: Optional[str] = None
    lat: float
    lng: float
    speed: Optional[float] = None
    heading: Optional[float] = None
    timestamp: datetime
    vehicle_plate: Optional[str] = None
    vehicle_brand: Optional[str] = None
    vehicle_model: Optional[str] = None
    driver_name: Optional[str] = None
    destination: Optional[str] = None
    origin_lat: Optional[float] = None
    origin_lng: Optional[float] = None
    destination_lat: Optional[float] = None
    destination_lng: Optional[float] = None


class JourneySimulationRequest(BaseModel):
    """Schema for simulating vehicle movement"""
    vehicle_id: UUID
    booking_id: UUID
    duration_seconds: int = 60  # Total simulation duration
    update_interval: int = 5  # Seconds between updates


class SeedJourneyData(BaseModel):
    """Schema for seeding sample journey data"""
    count: int = 3  # Number of vehicles to seed


class LocationHistoryPoint(BaseModel):
    """A single point in location history"""
    lat: float
    lng: float
    timestamp: datetime
    speed: Optional[float] = None
