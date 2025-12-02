# src/etl/data_ingestion.py
import logging
from typing import Tuple, List

import pandas as pd

logger = logging.getLogger(__name__)


class FreightDataIngestion:
    """Handles loading and validating raw freight data."""

    REQUIRED_COLUMNS = [
        "shipment_id",
        "route",
        "carrier",
        "weight_kg",
        "date",
        "rate_per_kg",
    ]

    @staticmethod
    def ingest_from_csv(path: str) -> pd.DataFrame:
        """Load freight data from a CSV file."""
        try:
            df = pd.read_csv(path)
            logger.info("Ingested %d rows from %s", len(df), path)
            return df
        except Exception as exc:
            logger.error("Failed to read CSV %s: %s", path, exc)
            return pd.DataFrame()

    @classmethod
    def validate(cls, df: pd.DataFrame) -> Tuple[pd.DataFrame, List[str]]:
        """Basic data-quality checks. Returns (df, issues)."""
        issues: List[str] = []

        # 1) Required columns present
        missing_cols = [c for c in cls.REQUIRED_COLUMNS if c not in df.columns]
        if missing_cols:
            issues.append(f"missing required columns: {missing_cols}")

        if df.empty:
            issues.append("dataframe is empty")

        # 2) Duplicates on shipment_id
        if "shipment_id" in df.columns:
            dup_count = df.duplicated(subset=["shipment_id"]).sum()
            if dup_count:
                issues.append(f"{dup_count} duplicate shipment_id rows")

        # 3) Nulls in required columns
        if not df.empty:
            nulls = df[cls.REQUIRED_COLUMNS].isnull().sum()
            if nulls.sum() > 0:
                issues.append(f"nulls in required columns: {nulls.to_dict()}")

        # 4) Simple numeric sanity checks
        if "rate_per_kg" in df.columns:
            bad_rates = df[(df["rate_per_kg"] <= 0) | (df["rate_per_kg"] > 10)]
            if len(bad_rates) > 0:
                issues.append(f"{len(bad_rates)} rows with weird rate_per_kg")

        if issues:
            logger.warning("Validation issues: %s", issues)
        else:
            logger.info("Data validation passed with no issues")

        return df, issues
