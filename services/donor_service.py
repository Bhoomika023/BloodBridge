"""Donor service: CRUD operations and donor matching."""
import logging

from database.db_connection import get_connection
from models.donor_model import Donor
from mysql.connector import Error
from services.blood_compatibility import compatible_donor_groups
from services.validation import normalize_blood_group, normalize_text, validate_age, validate_phone_number


logger = logging.getLogger(__name__)


ALLOWED_DONOR_UPDATE_FIELDS = {
    "full_name",
    "age",
    "gender",
    "blood_group",
    "city",
    "district",
    "state",
    "availability_status",
    "contact_number",
    "email",
    "last_donation_date",
}


class DonorService:
    @staticmethod
    def _column_exists(cur, table_name, column_name):
        cur.execute(
            """
            SELECT COUNT(*)
            FROM information_schema.columns
            WHERE table_schema = DATABASE() AND table_name=%s AND column_name=%s
            """,
            (table_name, column_name),
        )
        return cur.fetchone()[0] > 0

    @staticmethod
    def add_donor(donor: Donor) -> bool:
        try:
            donor.full_name = normalize_text(donor.full_name)
            donor.city = normalize_text(donor.city)
            donor.contact_number = validate_phone_number(donor.contact_number)
            donor.age = validate_age(donor.age)
            donor.blood_group = normalize_blood_group(donor.blood_group)
            with get_connection() as conn:
                cur = conn.cursor()
                columns = [
                    "full_name",
                    "age",
                    "gender",
                    "blood_group",
                    "city",
                    "district",
                    "state",
                    "availability_status",
                    "contact_number",
                    "email",
                    "last_donation_date",
                ]
                values = [
                    donor.full_name,
                    donor.age,
                    donor.gender,
                    donor.blood_group,
                    donor.city,
                    donor.district,
                    donor.state,
                    donor.availability_status,
                    donor.contact_number,
                    donor.email,
                    donor.last_donation_date,
                ]
                if DonorService._column_exists(cur, "donor", "phone"):
                    columns.insert(9, "phone")
                    values.insert(9, donor.contact_number)
                placeholders = ",".join(["%s"] * len(columns))
                sql = f"INSERT INTO donor ({','.join(columns)}) VALUES ({placeholders})"
                cur.execute(sql, tuple(values))
                conn.commit()
                return True
        except Error:
            logger.exception("Add donor failed")
            return False

    @staticmethod
    def get_all_donors():
        sql = """
        SELECT donor_id, full_name, age, gender, blood_group, city, district, state,
               availability_status, contact_number, email, last_donation_date
        FROM donor
        ORDER BY city, blood_group, full_name
        """
        try:
            with get_connection() as conn:
                cur = conn.cursor()
                cur.execute(sql)
                return cur.fetchall()
        except Error:
            logger.exception("Get donors failed")
            return []

    @staticmethod
    def search_donors(name=None, blood_group=None, city=None, status=None):
        name = normalize_text(name)
        city = normalize_text(city)
        blood_group = normalize_blood_group(blood_group) if blood_group else None
        sql = """
        SELECT donor_id, full_name, age, gender, blood_group, city, district, state,
               availability_status, contact_number, email, last_donation_date
        FROM donor WHERE 1=1
        """
        params = []
        if name:
            sql += " AND full_name LIKE %s"
            params.append(f"%{name}%")
        if blood_group:
            sql += " AND blood_group = %s"
            params.append(blood_group)
        if city:
            sql += " AND city LIKE %s"
            params.append(f"%{city}%")
        if status:
            sql += " AND availability_status = %s"
            params.append(status)
        sql += " ORDER BY city, blood_group, full_name"
        try:
            with get_connection() as conn:
                cur = conn.cursor()
                cur.execute(sql, tuple(params))
                return cur.fetchall()
        except Error:
            logger.exception("Search donors failed")
            return []

    @staticmethod
    def find_matching_donors(blood_group, city, only_available=False):
        blood_group = normalize_blood_group(blood_group)
        city = normalize_text(city)
        compatible_groups = compatible_donor_groups(blood_group)
        if not compatible_groups:
            return []

        group_placeholders = ",".join(["%s"] * len(compatible_groups))
        sql = f"""
         SELECT donor_id, full_name, contact_number, blood_group, city, district, state, last_donation_date, availability_status,
               CASE WHEN blood_group=%s THEN 'Exact Match' ELSE 'Compatible Match' END AS match_type
        FROM donor
        WHERE blood_group IN ({group_placeholders})
        """
        params = [blood_group, *compatible_groups]
        if only_available:
            sql += " AND availability_status='Available'"
        sql += """
        ORDER BY
          CASE WHEN blood_group=%s THEN 0 ELSE 1 END,
          CASE WHEN city=%s THEN 0 ELSE 1 END,
                    CASE WHEN district IS NULL OR district='' THEN 1 ELSE 0 END,
          FIELD(availability_status, 'Available', 'Recently Donated', 'Inactive'),
          CASE WHEN last_donation_date IS NULL THEN 1 ELSE 0 END,
          last_donation_date ASC,
          full_name
        LIMIT 25
        """
        params.extend([blood_group, city])
        try:
            with get_connection() as conn:
                cur = conn.cursor()
                cur.execute(sql, tuple(params))
                return cur.fetchall()
        except Error:
            logger.exception("Find matching donors failed")
            return []

    @staticmethod
    def update_donor(donor_id, **fields):
        if not fields:
            return False
        invalid_fields = set(fields) - ALLOWED_DONOR_UPDATE_FIELDS
        if invalid_fields:
            logger.warning("Rejected donor update with invalid fields: %s", sorted(invalid_fields))
            return False
        if "age" in fields:
            fields["age"] = validate_age(fields["age"])
        if "contact_number" in fields:
            fields["contact_number"] = validate_phone_number(fields["contact_number"])
        if "blood_group" in fields:
            fields["blood_group"] = normalize_blood_group(fields["blood_group"])
        set_clause = ", ".join(f"{k}=%s" for k in fields.keys())
        sql = f"UPDATE donor SET {set_clause} WHERE donor_id=%s"
        params = list(fields.values()) + [donor_id]
        try:
            with get_connection() as conn:
                cur = conn.cursor()
                cur.execute(sql, tuple(params))
                conn.commit()
                return True
        except Error:
            logger.exception("Update donor failed")
            return False

    @staticmethod
    def delete_donor(donor_id):
        sql = "DELETE FROM donor WHERE donor_id=%s"
        try:
            with get_connection() as conn:
                cur = conn.cursor()
                cur.execute(sql, (donor_id,))
                conn.commit()
                return True
        except Error:
            logger.exception("Delete donor failed")
            return False
