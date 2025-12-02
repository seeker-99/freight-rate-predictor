# src/database/queries.py
from datetime import date, timedelta
from typing import List, Dict, Tuple

from sqlalchemy import func, and_
from sqlalchemy.orm import Session

from .models import Shipment, RatePrediction, RouteMetric, CarrierMetric


def get_historical_rates(
    db: Session, route: str, days: int = 30
) -> List[Dict]:
    cutoff = date.today() - timedelta(days=days)
    rows = (
        db.query(
            Shipment.date.label("d"),
            func.avg(Shipment.rate_per_kg).label("avg_rate"),
            func.min(Shipment.rate_per_kg).label("min_rate"),
            func.max(Shipment.rate_per_kg).label("max_rate"),
            func.count(Shipment.id).label("cnt"),
        )
        .filter(and_(Shipment.route == route, Shipment.date >= cutoff))
        .group_by(Shipment.date)
        .order_by(Shipment.date)
        .all()
    )
    return [
        {
            "date": str(r.d),
            "avg_rate": float(r.avg_rate),
            "min_rate": float(r.min_rate),
            "max_rate": float(r.max_rate),
            "shipment_count": int(r.cnt),
        }
        for r in rows
    ]


def get_carrier_stats(db: Session, carrier: str) -> Dict | None:
    row = (
        db.query(
            func.avg(Shipment.rate_per_kg).label("avg_rate"),
            func.count(Shipment.id).label("total_shipments"),
            func.sum(
                func.case((Shipment.status == "delivered", 1), else_=0)
            ).label("delivered"),
        )
        .filter(Shipment.carrier == carrier)
        .first()
    )
    if not row or row.total_shipments == 0:
        return None
    on_time_pct = float(row.delivered) / row.total_shipments * 100.0
    return {
        "carrier": carrier,
        "avg_rate": float(row.avg_rate),
        "total_shipments": int(row.total_shipments),
        "on_time_percentage": on_time_pct,
        "reliability_score": on_time_pct,
    }


def get_latest_predictions(
    db: Session, route: str, days_ahead: int = 7
) -> List[Dict]:
    today = date.today()
    rows = (
        db.query(RatePrediction)
        .filter(
            and_(
                RatePrediction.route == route,
                RatePrediction.prediction_date >= today,
            )
        )
        .order_by(RatePrediction.prediction_date)
        .all()
    )
    return [
        {
            "date": str(r.prediction_date),
            "predicted_rate": float(r.predicted_rate),
            "confidence_lower": float(r.confidence_lower)
            if r.confidence_lower is not None
            else None,
            "confidence_upper": float(r.confidence_upper)
            if r.confidence_upper is not None
            else None,
        }
        for r in rows
    ]


def store_predictions(
    db: Session,
    route: str,
    predictions: List[Tuple[date, float, float, float]],
    model_version: str = "v1",
) -> None:
    for pred_date, rate, low, high in predictions:
        rec = RatePrediction(
            route=route,
            prediction_date=pred_date,
            predicted_rate=rate,
            confidence_lower=low,
            confidence_upper=high,
            model_version=model_version,
        )
        db.add(rec)
    db.commit()


def get_route_metrics(db: Session) -> List[Dict]:
    rows = db.query(RouteMetric).order_by(RouteMetric.avg_rate.desc()).all()
    return [
        {
            "route": r.route,
            "avg_rate": float(r.avg_rate),
            "min_rate": float(r.min_rate),
            "max_rate": float(r.max_rate),
            "shipment_count": int(r.shipment_count),
        }
        for r in rows
    ]
