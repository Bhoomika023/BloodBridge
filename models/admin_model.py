"""
Admin model.
"""

class Admin:
    def __init__(self, username, password_hash, admin_id=None):
        self.admin_id = admin_id
        self.username = username
        self.password_hash = password_hash
