# tests/unit/test_etl.py
import pandas as pd

from src.etl.data_ingestion import FreightDataIngestion
from src.etl.data_cleaning import FreightDataCleaning


def test_validation_no_issues():
    df = pd.DataFrame(
        {
            "shipment_id": ["S1", "S2"],
            "route": ["NYC-LA", "NYC-CHI"],
            "carrier": ["FedEx", "UPS"],
            "weight_kg": [1000, 1500],
            "date": ["2024-01-01", "2024-01-02"],
            "rate_per_kg": [2.5, 1.8],
            "status": ["delivered", "delivered"],
            "distance_km": [2000, 1500],
            "days_to_delivery": [3, 4],
        }
    )
    _, issues = FreightDataIngestion.validate(df)
    assert issues == []


def test_validation_reports_issues():
    df = pd.DataFrame(
        {
            "shipment_id": ["S1", "S1"],
            "route": ["NYC-LA", "NYC-LA"],
            "carrier": ["FedEx", "FedEx"],
            "weight_kg": [1000, None],
            "date": ["2024-01-01", None],
            "rate_per_kg": [2.5, -1.0],
            "status": ["delivered", None],
            "distance_km": [2000, 1500],
            "days_to_delivery": [3, None],
        }
    )
    _, issues = FreightDataIngestion.validate(df)
    assert len(issues) >= 1


def test_cleaning_removes_duplicates():
    df = pd.DataFrame(
        {
            "shipment_id": ["S1", "S1", "S2"],
            "route": ["NYC-LA", "NYC-LA", "NYC-CHI"],
            "carrier": ["FedEx", "FedEx", "UPS"],
            "weight_kg": [1000, 1000, 1500],
            "date": ["2024-01-01", "2024-01-01", "2024-01-02"],
            "rate_per_kg": [2.5, 2.5, 1.8],
            "status": ["delivered", "delivered", "delivered"],
            "distance_km": [2000, 2000, 1500],
            "days_to_delivery": [3, 3, 4],
        }
    )
    cleaned = FreightDataCleaning.clean(df)
    assert len(cleaned) == 2  # one duplicate removed


def test_feature_engineering_columns_present():
    df = pd.DataFrame(
        {
            "shipment_id": ["S1"],
            "route": ["NYC-LA"],
            "carrier": ["FedEx"],
            "weight_kg": [1000],
            "date": ["2024-01-01"],
            "rate_per_kg": [2.5],
            "status": ["delivered"],
            "distance_km": [2000],
            "days_to_delivery": [3],
        }
    )
    df["date"] = pd.to_datetime(df["date"])
