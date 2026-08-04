"""Donation history service."""
import logging

from database.db_connection import get_connection
from mysql.connector import Error


logger = logging.getLogger(__name__)


class DonationService:
    @staticmethod
    def get_history(limit=100, filters=None):
        filters = filters or {}
        sql = """
        SELECT h.donation_id, d.full_name, d.blood_group, d.city, h.units_donated, h.donation_date, COALESCE(h.hospital_name, '')
        FROM donation_history h
        JOIN donor d ON d.donor_id = h.donor_id
        WHERE 1=1
        """
        params = []
        if filters.get("donor"):
            sql += " AND d.full_name LIKE %s"
            params.append(f"%{filters['donor'].strip()}%")
        if filters.get("blood_group"):
            sql += " AND d.blood_group=%s"
            params.append(filters["blood_group"])
        if filters.get("city"):
            sql += " AND d.city LIKE %s"
            params.append(f"%{filters['city'].strip()}%")
        if filters.get("hospital"):
            sql += " AND COALESCE(h.hospital_name, '') LIKE %s"
            params.append(f"%{filters['hospital'].strip()}%")
        if filters.get("date"):
            sql += " AND h.donation_date=%s"
            params.append(filters["date"])
        sql += " ORDER BY h.donation_date DESC, h.donation_id DESC LIMIT %s"
        try:
            with get_connection() as conn:
                cur = conn.cursor()
                cur.execute(sql, tuple(params + [limit]))
                return cur.fetchall()
        except Error:
            logger.exception("Donation history query failed")
            return []
