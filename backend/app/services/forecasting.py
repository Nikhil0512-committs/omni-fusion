import numpy as np
from datetime import datetime, timedelta, timezone
from typing import List

class ForecastingService:
    @staticmethod
    def generate_forecast(historical_scores: List[float], historical_dates: List[datetime]):
        """
        Generates a 3-point future trajectory (+1m, +3m, +6m) using exponential smoothing.
        Refuses to forecast if there are fewer than 3 historical data points.
        """
        if len(historical_scores) < 3:
            return {
                "forecast": [],
                "confidence": "Low",
                "message": "Insufficient historical data for reliable forecasting. Need at least 3 data points."
            }

        # Simple Exponential Smoothing (Holt's linear trend method approximation)
        # Using numpy to calculate a simple linear regression over time to project future
        
        # Convert dates to days since first prediction
        base_date = historical_dates[0]
        days = np.array([(d - base_date).days for d in historical_dates])
        scores = np.array(historical_scores)
        
        # We need variance in days to compute trend
        if days[-1] - days[0] == 0:
            # All on the same day, can't reliably project trend
            return {
                "forecast": [],
                "confidence": "Low",
                "message": "Data points are too close in time. Need longitudinal data spanning multiple days."
            }

        # Fit a line: score = m * day + c
        m, c = np.polyfit(days, scores, 1)
        
        # Generate future points
        last_date = historical_dates[-1]
        future_offsets_days = [30, 90, 180] # +1m, +3m, +6m
        
        forecast = []
        for offset in future_offsets_days:
            future_day = days[-1] + offset
            projected_score = m * future_day + c
            # Clip between 0 and 1
            projected_score = max(0.0, min(1.0, projected_score))
            
            future_date = last_date + timedelta(days=offset)
            
            # Simple confidence bounds (widening over time)
            # In a real model, this would be std error of prediction
            margin = 0.05 + (offset / 180) * 0.1
            
            forecast.append({
                "date": future_date.isoformat(),
                "projected_risk": float(projected_score),
                "lower_bound": float(max(0.0, projected_score - margin)),
                "upper_bound": float(min(1.0, projected_score + margin))
            })
            
        return {
            "forecast": forecast,
            "confidence": "Medium" if len(historical_scores) < 5 else "High",
            "message": "Forecast generated successfully."
        }
