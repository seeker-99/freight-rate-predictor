# tests/unit/test_models.py
import pandas as pd
from datetime import date, timedelta
from src.models.arima_predictor import ARIMAPredictor


def _sample_series(n: int = 120):
    dates = pd.date_range(start="2023-01-01", periods=n, freq="D")
    # simple upward trend with small noise
    rates = [2.0 + 0.001 * i for i in range(n)]
    return rates, dates


def test_model_train_and_predict():
    rates, dates = _sample_series()
    model = ARIMAPredictor(order=(1, 1, 1))
    ok = model.train(rates, dates)
    assert ok is True
    preds = model.predict(steps=7)
    assert len(preds) == 7
    for p in preds:
        assert 0.5 <= p["predicted_rate"] <= 5.0
        assert isinstance(p["date"], date)
