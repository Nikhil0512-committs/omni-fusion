"""Regression tests for doctor-link HTTP error preservation."""

import asyncio

import pytest
from fastapi import HTTPException

from app.api.v1 import doctor_links
from app.models.profile_schemas import LinkStatusUpdate


class _EmptyUpdate:
    data = []

    def update(self, _value): return self
    def eq(self, _field, _value): return self
    def execute(self): return self


class _FakeSupabase:
    def table(self, _name): return _EmptyUpdate()


def test_invalid_link_update_remains_404(monkeypatch):
    monkeypatch.setattr(doctor_links, "supabase", _FakeSupabase())
    user_data = {"auth": type("User", (), {"id": "doctor-id"})()}
    with pytest.raises(HTTPException) as raised:
        asyncio.run(doctor_links.update_link_status.__wrapped__(
            "missing-link",
            LinkStatusUpdate(status="accepted"),
            user_data,
        ))
    assert raised.value.status_code == 404
