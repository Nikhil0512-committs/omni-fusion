import pytest
from unittest.mock import MagicMock
from app.core.supabase_client import supabase

@pytest.fixture(autouse=True)
def mock_supabase(monkeypatch):
    mock_table = MagicMock()
    
    # Mock for predict insertion and analytics
    mock_table.return_value.insert.return_value.execute.return_value = MagicMock()
    
    # Mock for history query
    mock_res = MagicMock()
    mock_res.count = 1
    mock_res.data = [{
        "id": "test_id",
        "created_at": "2024-01-01T00:00:00",
        "risk_score": 0.15,
        "streams_used": ["ecg"],
        "reports": [],
        "patient_id": "test_user_id"
    }]
    mock_table.return_value.select.return_value.execute.return_value = mock_res
    mock_table.return_value.select.return_value.eq.return_value.execute.return_value = mock_res
    mock_table.return_value.select.return_value.eq.return_value.eq.return_value.execute.return_value = mock_res
    mock_table.return_value.select.return_value.eq.return_value.eq.return_value.single.return_value.execute.return_value = mock_res
    mock_table.return_value.select.return_value.eq.return_value.order.return_value.range.return_value.execute.return_value = mock_res
    mock_storage_bucket = MagicMock()
    mock_storage_bucket.get_public_url.return_value = "http://test-url.com/report.pdf"
    mock_storage_bucket.create_signed_url.return_value = {"signedURL": "http://test-url.com/signed.pdf"}
    
    # Patch the table method on the real supabase client so any module that imported it gets the mock
    monkeypatch.setattr(supabase, "table", mock_table)
    # Patch the from_ method on the returned storage client
    monkeypatch.setattr(supabase.storage, "from_", MagicMock(return_value=mock_storage_bucket))
    
    # Patch dependencies globally
    from app.main import app
    from app.core.auth import get_current_user, get_optional_current_user
    
    app.dependency_overrides[get_current_user] = lambda: {
        "auth": MagicMock(id="test_user_id"),
        "profile": {"role": "PATIENT"}
    }
    
    app.dependency_overrides[get_optional_current_user] = lambda: None
    
    yield mock_table
