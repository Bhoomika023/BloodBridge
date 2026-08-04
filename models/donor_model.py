"""
Donor model class.
Simple dataclass-like structure to move data between layers.
"""
from datetime import date


class Donor:
    def __init__(
        self,
        full_name,
        age,
        gender,
        blood_group,
        city,
        contact_number,
        email=None,
        district=None,
        state="Karnataka",
        availability_status="Available",
        last_donation_date: date = None,
        donor_id=None,
    ):
        self.donor_id = donor_id
        self.full_name = full_name
        self.age = age
        self.gender = gender
        self.blood_group = blood_group
        self.city = city
        self.district = district
        self.state = state
        self.availability_status = availability_status
        self.contact_number = contact_number
        self.phone = contact_number
        self.email = email
        self.last_donation_date = last_donation_date
