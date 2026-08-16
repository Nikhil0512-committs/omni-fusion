import pytest
from datetime import datetime, timedelta, timezone
from app.services.forecasting import ForecastingService

def test_forecasting_insufficient_data():
    dates = [datetime.now(timezone.utc)]
    scores = [0.4]
    
    result = ForecastingService.generate_forecast(scores, dates)
    assert result["confidence"] == "Low"
    assert len(result["forecast"]) == 0
    assert "Need at least 3" in result["message"]

def test_forecasting_same_day():
    now = datetime.now(timezone.utc)
    dates = [now, now, now]
    scores = [0.4, 0.45, 0.5]
    
    result = ForecastingService.generate_forecast(scores, dates)
    assert result["confidence"] == "Low"
    assert len(result["forecast"]) == 0
    assert "span" in result["message"].lower() or "multiple days" in result["message"].lower()

def test_forecasting_valid():
    now = datetime.now(timezone.utc)
    dates = [now - timedelta(days=90), now - timedelta(days=60), now - timedelta(days=30), now]
    # Upward trend
    scores = [0.3, 0.4, 0.5, 0.6]
    
    result = ForecastingService.generate_forecast(scores, dates)
    assert result["confidence"] in ["Medium", "High"]
    assert len(result["forecast"]) == 3
    
    # Check that +1m, +3m, +6m are present and ascending
    f1, f2, f3 = result["forecast"]
    assert f3["projected_risk"] > f1["projected_risk"]
    assert f1["projected_risk"] > 0.6
