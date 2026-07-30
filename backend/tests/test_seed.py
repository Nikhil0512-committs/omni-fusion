import pytest
from unittest.mock import MagicMock, patch

import unittest

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

@patch('httpx.get')
@patch('httpx.post')
@patch('scripts.seed_demo_accounts.os.remove')
@patch('scripts.seed_demo_accounts.supabase')
@patch('scripts.seed_demo_accounts.inference_service')
@patch('scripts.seed_demo_accounts.pdf_service')
def test_seed_demo_accounts_idempotency(mock_pdf, mock_inference, mock_supabase, mock_remove, mock_httpx_post, mock_httpx_get, capsys):
    from scripts.seed_demo_accounts import seed_users
    
    # Mock behavior for first run (users don't exist)
    mock_supabase.table().select().eq().execute.return_value = MagicMock(data=[])
    
    # Mock auth create_user (httpx bypass)
    mock_auth_res = MagicMock()
    mock_auth_res.json.return_value = {"id": "mock-uuid"}
    mock_auth_res.raise_for_status.return_value = None
    mock_httpx_post.return_value = mock_auth_res
    
    # Mock inference
    mock_pred = MagicMock()
    mock_pred.risk_score = 0.8
    mock_pred.streams_used = ["ecg", "vitals"]
    mock_pred.shap_data = {"Vital_HR": 0.5}
    mock_pred.failure_analysis_summary = "Test"
    mock_inference.predict.return_value = mock_pred
    
    # Mock PDF
    mock_pdf.generate_report.return_value = "/tmp/mock.pdf"
    mock_supabase.storage.from_().create_signed_url.return_value = {"signedURL": "http://mock"}
    
    with patch('builtins.open', unittest.mock.mock_open(read_data=b"data")):
        seed_users()
    
    captured = capsys.readouterr()
    assert "Creating Doctor" in captured.out
    assert "Creating Patient" in captured.out
    
    # Second run (users exist)
    # Return mock data indicating they exist
    mock_supabase.table().select().eq().execute.return_value = MagicMock(data=[{"id": "mock-uuid"}])
    
    seed_users()
    
    captured_second = capsys.readouterr()
    assert "already exists. Skipping creation." in captured_second.out
    assert "Creating Doctor" not in captured_second.out.replace(captured.out, "")
