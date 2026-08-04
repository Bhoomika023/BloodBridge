"""Reusable input validation helpers for the dashboard and services."""

from __future__ import annotations

import re

from services.location_data import BLOOD_GROUPS


PHONE_PATTERN = re.compile(r"^[6-9]\d{9}$|^\d{6,15}$")
VALID_BLOOD_GROUPS = {group.upper() for group in BLOOD_GROUPS}


def normalize_text(value: str) -> str:
    """Strip whitespace and collapse empty values to an empty string."""

    return (value or "").strip()


def require_text(value: str, field_name: str) -> str:
    """Validate that a field is present and not just whitespace."""

    cleaned = normalize_text(value)
    if not cleaned:
        raise ValueError(f"{field_name} is required")
    return cleaned


def validate_phone_number(value: str) -> str:
    """Validate a phone number in either Indian mobile or generic digit form."""

    cleaned = normalize_text(value)
    if not PHONE_PATTERN.fullmatch(cleaned):
        raise ValueError("invalid phone number")
    return cleaned


def validate_age(value: str, minimum: int = 18, maximum: int = 65) -> int:
    """Validate an integer age within an inclusive range."""

    number = int(str(value).strip())
    if number < minimum or number > maximum:
        raise ValueError("age outside allowed range")
    return number


def validate_units(value: str, minimum: int = 1, maximum: int = 20) -> int:
    """Validate requested or donated blood units."""

    number = int(str(value).strip())
    if number < minimum or number > maximum:
        raise ValueError("units outside allowed range")
    return number


def normalize_blood_group(value: str) -> str:
    """Validate and normalize a blood group label."""

    cleaned = normalize_text(value).upper()
    if cleaned not in VALID_BLOOD_GROUPS:
        raise ValueError("invalid blood group")
    return cleaned
