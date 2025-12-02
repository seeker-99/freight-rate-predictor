# src/etl/data_cleaning.py
import logging

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


class FreightDataCleaning:
    """Cleans and enriches freight shipment data."""

    @staticmethod
    def clean(df: pd.DataFrame) -> pd.DataFrame:
        """Handle types, nulls, duplicates and simple outliers."""
        df = df.copy()

        # Ensure date is datetime
        if "date" in df.columns:
            df["date"] = pd.to_datetime(df["date"], errors="coerce")

        # Drop rows with completely broken dates
        before = len(df)
        df = df.dropna(subset=["date"])
        logger.info("Dropped %d rows with invalid dates", before - len(df))

        # Fill numeric nulls (median) for key fields
        for col in ["weight_kg", "rate_per_kg", "distance_km"]:
            if col in df.columns and df[col].isnull().any():
                median = df[col].median()
                df[col] = df[col].fillna(median)

        # Fill status
        if "status" in df.columns:
            df["status"] = df["status"].fillna("unknown")

        # Remove duplicate shipment_ids
        if "shipment_id" in df.columns:
            before = len(df)
            df = df.drop_duplicates(subset=["shipment_id"], keep="first")
            logger.info("Removed %d duplicate shipments", before - len(df))

        # Clip obviously bad values
        if "rate_per_kg" in df.columns:
            df["rate_per_kg"] = df["rate_per_kg"].clip(lower=0.5, upper=5.0)
        if "weight_kg" in df.columns:
            df["weight_kg"] = df["weight_kg"].clip(lower=50, upper=10000)

        logger.info("Cleaned dataframe now has %d rows", len(df))
        return df

    @staticmethod
    def add_features(df: pd.DataFrame) -> pd.DataFrame:
        """Add engineered features useful for analytics / models."""
        df = df.copy()

        if "date" in df.columns:
            df["month"] = df["date"].dt.month
            df["day_of_week"] = df["date"].dt.dayofweek
            df["quarter"] = df["date"].dt.quarter
            df["is_weekend"] = df["day_of_week"].isin([5, 6]).astype(int)

        if {"rate_per_kg", "weight_kg"}.issubset(df.columns):
            df["shipment_cost"] = df["rate_per_kg"] * df["weight_kg"]
            df["rate_per_ton"] = df["rate_per_kg"] * 1000

        if "weight_kg" in df.columns:
            df["weight_bucket"] = pd.cut(
                df["weight_kg"],
                bins=[0, 500, 2000, 10000],
                labels=["light", "medium", "heavy"],
            )

        logger.info("Added engineered features")
        return df
