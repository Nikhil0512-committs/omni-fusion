import os
import pytest
from pydantic import ValidationError

def test_config_missing_required_env_var(monkeypatch):
    """
    Test that the application fails fast if required environment variables are missing.
    We temporarily unset SUPABASE_URL and try to instantiate Settings.
    """
    monkeypatch.delenv("SUPABASE_URL", raising=False)
    
    # We must import inside the test because Settings is evaluated on import in config.py.
    # To isolate it, we can import the Settings class directly.
    from app.core.config import Settings
    
    with pytest.raises(ValidationError) as exc_info:
        Settings(_env_file=None)
    
    assert "SUPABASE_URL" in str(exc_info.value) or "supabase_url" in str(exc_info.value)
    assert "cannot be empty" in str(exc_info.value) or "Field required" in str(exc_info.value)
