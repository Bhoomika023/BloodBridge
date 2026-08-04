"""
Stock model.
"""

class Stock:
    def __init__(self, blood_group, units_available, stock_id=None):
        self.stock_id = stock_id
        self.blood_group = blood_group
        self.units_available = units_available
