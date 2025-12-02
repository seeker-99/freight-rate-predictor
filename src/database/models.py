# src/database/models.py
from sqlalchemy import Column, Integer, String, Float, Date, DateTime
from sqlalchemy.orm import declarative_base
from datetime import datetime

Base = declarative_base()


class Shipment(Base):
    __tablename__ = "shipments"

    id = Column(Integer, primary_key=True, index=True)
    shipment_id = Column(String(50), unique=True, nullable=False, index=True)
    route = Column(String(50), nullable=False, index=True)
    carrier = Column(String(100), nullable=False, index=True)
    weight_kg = Column(Float, nullable=False)
    date = Column(Date, nullable=False, index=True)
    rate_per_kg = Column(Float, nullable=False)
    status = Column(String(20), nullable=False)
    distance_km = Column(Integer)
    days_to_delivery = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow)


class RatePrediction(Base):
    __tablename__ = "rate_predictions"

    id = Column(Integer, primary_key=True, index=True)
    route = Column(String(50), nullable=False, index=True)
    prediction_date = Column(Date, nullable=False, index=True)
    predicted_rate = Column(Float, nullable=False)
    confidence_lower = Column(Float)
    confidence_upper = Column(Float)
    model_version = Column(String(20))
    created_at = Column(DateTime, default=datetime.utcnow)


class RouteMetric(Base):
    __tablename__ = "route_metrics"

    id = Column(Integer, primary_key=True, index=True)
    route = Column(String(50), unique=True, nullable=False, index=True)
    avg_rate = Column(Float)
    min_rate = Column(Float)
    max_rate = Column(Float)
    shipment_count = Column(Integer)
    on_time_percentage = Column(Float)
    last_updated = Column(DateTime, default=datetime.utcnow)


class CarrierMetric(Base):
    __tablename__ = "carrier_metrics"

    id = Column(Integer, primary_key=True, index=True)
    carrier = Column(String(100), unique=True, nullable=False, index=True)
    avg_rate = Column(Float)
    on_time_percentage = Column(Float)
    shipment_count = Column(Integer)
    reliability_score = Column(Float)
    last_updated = Column(DateTime, default=datetime.utcnow)
