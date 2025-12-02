# src/api/routes.py
from fastapi import APIRouter, HTTPException, Query
from datetime import datetime, date, timedelta
from typing import List
from src.api.schemas import (
    RatePredictionResponse,
    HistoricalRateResponse,
    HistoricalRatePoint,
    CarrierStatsResponse,
    BulkPredictionItem,
    BulkPredictionResponse,
)

router = APIRouter()

@router.get("/predict", response_model=RatePredictionResponse)
def predict_rate(
    route: str = Query(..., description="Route code, e.g. NYC-LA"),
    weight_kg: float = Query(..., ge=50, le=10000),
):
    """Simple placeholder prediction (wire up real DB/model later)."""
    base_rate = 2.5
    predicted_rate = base_rate
    return RatePredictionResponse(
        route=route,
        weight_kg=weight_kg,
        predicted_rate=predicted_rate,
        confidence_lower=predicted_rate * 0.9,
        confidence_upper=predicted_rate * 1.1,
        prediction_date=str(date.today() + timedelta(days=1)),
        total_cost=predicted_rate * weight_kg,
    )

@router.get("/historical/{route}", response_model=HistoricalRateResponse)
def get_historical(route: str, days: int = 30):
    """Dummy historical series so endpoint works."""
    today = date.today()
    records: List[HistoricalRatePoint] = []
    for i in range(days):
        d = today - timedelta(days=i)
        records.append(
            HistoricalRatePoint(
                date=str(d),
                avg_rate=2.5,
                min_rate=2.3,
                max_rate=2.7,
                shipment_count=10,
            )
        )
    records = list(reversed(records))
    summary = {
        "avg_rate": 2.5,
        "min_rate": 2.3,
        "max_rate": 2.7,
        "total_shipments": sum(r.shipment_count for r in records),
    }
    return HistoricalRateResponse(
        route=route, period_days=days, records=records, summary=summary
    )

@router.get("/carriers/{carrier}", response_model=CarrierStatsResponse)
def get_carrier(carrier: str):
    return CarrierStatsResponse(
        carrier=carrier,
        avg_rate=2.4,
        total_shipments=100,
        on_time_percentage=95.0,
        reliability_score=95.0,
    )

@router.get("/routes")
def list_routes():
    return {
        "total_routes": 3,
        "routes": [
            {"route": "NYC-LA", "avg_rate": 2.5},
            {"route": "NYC-CHI", "avg_rate": 1.8},
            {"route": "LA-SEA", "avg_rate": 1.2},
        ],
    }

@router.post("/bulk-predict", response_model=BulkPredictionResponse)
def bulk_predict(
    routes: List[str] = Query(...),
    weight_kg: float = Query(..., ge=50, le=10000),
):
    items = []
    for r in set(routes):
        rate = 2.5
        items.append(BulkPredictionItem(route=r, predicted_rate=rate, total_cost=rate * weight_kg))
    return BulkPredictionResponse(
        weight_kg=weight_kg,
        predictions=items,
        errors=None,
        timestamp=datetime.utcnow(),
    )
