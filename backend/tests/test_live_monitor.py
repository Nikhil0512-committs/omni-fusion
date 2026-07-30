import pytest
from fastapi.testclient import TestClient
from app.main import app
import asyncio

client = TestClient(app)

def test_live_monitor_websocket_lifecycle():
    # We will connect and disconnect
    patient_id = "test_patient_live"
    with client.websocket_connect(f"/api/v1/live-monitor/{patient_id}?token=dummy") as websocket:
        # Receive a few frames
        for _ in range(3):
            data = websocket.receive_json()
            assert "ecg" in data
            assert "spo2" in data
            assert "hr" in data
            assert "is_anomaly" in data
            
    # After disconnect, the websocket should close without throwing exceptions
