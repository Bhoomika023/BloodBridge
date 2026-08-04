"""
Blood request model.
"""
from datetime import date


class BloodRequest:
    def __init__(self, patient_name, blood_group, units_needed, hospital_name, request_date: date, status='Active', contact_number="", request_id=None):
        self.request_id = request_id
        self.patient_name = patient_name
        self.blood_group = blood_group
        self.units_needed = units_needed
        self.hospital_name = hospital_name
        self.request_date = request_date
        self.status = status
        self.contact_number = contact_number
