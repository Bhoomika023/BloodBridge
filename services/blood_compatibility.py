"""Reusable blood compatibility helpers.

The compatibility table below is written from the recipient's perspective:
each key is the blood group a patient needs, and the tuple lists donor blood
groups that can safely donate packed red blood cells to that recipient.

Rules encoded here follow standard transfusion compatibility:
- O- is the universal red-cell donor but can only receive O-.
- AB+ can receive from every compatible group.
- Rh-negative recipients only receive Rh-negative blood.
"""

from __future__ import annotations

from typing import Tuple


# Recipient -> compatible donor blood groups.
# This table is intentionally explicit so it is easy to audit in a college DBMS
# project and can be reused by services, UI helpers, and future reports.
RECIPIENT_COMPATIBLE_DONORS = {
    "O-": ("O-",),
    "O+": ("O-", "O+"),
    "A-": ("O-", "A-"),
    "A+": ("O-", "O+", "A-", "A+"),
    "B-": ("O-", "B-"),
    "B+": ("O-", "O+", "B-", "B+"),
    "AB-": ("O-", "A-", "B-", "AB-"),
    "AB+": ("O-", "O+", "A-", "A+", "B-", "B+", "AB-", "AB+"),
}


def compatible_donor_groups(recipient_blood_group: str) -> Tuple[str, ...]:
    """Return the medically compatible donor groups for a recipient."""

    normalized = (recipient_blood_group or "").upper().strip()
    return RECIPIENT_COMPATIBLE_DONORS.get(normalized, ())
