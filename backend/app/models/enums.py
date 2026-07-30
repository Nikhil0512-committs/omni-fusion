"""Shared string enums matching values persisted in Supabase."""

from enum import Enum


class Role(str, Enum):
    """Supported user roles."""

    DOCTOR = "DOCTOR"
    PATIENT = "PATIENT"


class LinkStatus(str, Enum):
    """Lifecycle states for doctor-patient links."""

    PENDING = "pending"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
