# src/api/schemas.py
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

class RatePredictionResponse(BaseModel):
    route: str
    weight_kg: float
    predicted_rate: float
    confidence_lower: float
    confidence_upper: float
    prediction_date: str
    total_cost: float

class HistoricalRatePoint(BaseModel):
    date: str
    avg_rate: float
    min_rate: float
    max_rate: float
    shipment_count: int

class HistoricalRateResponse(BaseModel):
    route: str
    period_days: int
    records: List[HistoricalRatePoint]
    summary: dict

class CarrierStatsResponse(BaseModel):
    carrier: str
    avg_rate: float
    total_shipments: int
    on_time_percentage: float
    reliability_score: float

class BulkPredictionItem(BaseModel):
    route: str
    predicted_rate: float
    total_cost: float

class BulkPredictionResponse(BaseModel):
    weight_kg: float
    predictions: List[BulkPredictionItem]
    errors: Optional[list] = None
    timestamp: datetime
