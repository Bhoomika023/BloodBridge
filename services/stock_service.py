"""
Stock service: view and update blood stock.
"""
import logging

from database.db_connection import get_connection
from mysql.connector import Error


logger = logging.getLogger(__name__)


class StockService:
    @staticmethod
    def get_all_stock():
        sql = "SELECT stock_id, blood_group, units_available FROM blood_stock ORDER BY blood_group"
        try:
            with get_connection() as conn:
                cur = conn.cursor()
                cur.execute(sql)
                return cur.fetchall()
        except Error:
            logger.exception("Get stock failed")
            return []

    @staticmethod
    def get_city_stock(city=None):
        sql = "SELECT stock_id, city, blood_group, units_available FROM city_stock"
        params = []
        if city:
            sql += " WHERE city LIKE %s"
            params.append(f"%{city}%")
        sql += " ORDER BY city, blood_group"
        try:
            with get_connection() as conn:
                cur = conn.cursor()
                cur.execute(sql, tuple(params))
                return cur.fetchall()
        except Error:
            logger.exception("Get city stock failed")
            return []

    @staticmethod
    def get_units_for_city(city, blood_group):
        sql = "SELECT COALESCE(units_available, 0) FROM city_stock WHERE city=%s AND blood_group=%s"
        try:
            with get_connection() as conn:
                cur = conn.cursor()
                cur.execute(sql, (city, blood_group))
                row = cur.fetchone()
                return row[0] if row else 0
        except Error:
            logger.exception("Get city units failed")
            return 0

    @staticmethod
    def update_city_stock(city, blood_group, delta, district="Mysuru", state="Karnataka"):
        try:
            with get_connection() as conn:
                cur = conn.cursor()
                cur.execute(
                    "SELECT units_available FROM city_stock WHERE city=%s AND blood_group=%s FOR UPDATE",
                    (city, blood_group),
                )
                row = cur.fetchone()
                if not row:
                    if delta < 0:
                        return False
                    cur.execute(
                        "INSERT INTO city_stock (city, district, state, blood_group, units_available) VALUES (%s,%s,%s,%s,%s)",
                        (city, district, state, blood_group, delta),
                    )
                else:
                    new_val = row[0] + delta
                    if new_val < 0:
                        return False
                    cur.execute(
                        "UPDATE city_stock SET units_available=%s WHERE city=%s AND blood_group=%s",
                        (new_val, city, blood_group),
                    )
                conn.commit()
                return True
        except Error:
            logger.exception("Update city stock failed")
            return False

    @staticmethod
    def low_stock_items(threshold=2):
        sql = """
        SELECT city, blood_group, units_available
        FROM city_stock
        WHERE units_available < %s
        ORDER BY units_available ASC, city, blood_group
        """
        try:
            with get_connection() as conn:
                cur = conn.cursor()
                cur.execute(sql, (threshold,))
                return cur.fetchall()
        except Error:
            logger.exception("Low stock query failed")
            return []

    @staticmethod
    def update_stock(blood_group, delta):
        """Increase/decrease units_available by delta. Uses transaction to avoid race conditions."""
        try:
            with get_connection() as conn:
                cur = conn.cursor()
                cur.execute("SELECT units_available FROM blood_stock WHERE blood_group=%s FOR UPDATE", (blood_group,))
                row = cur.fetchone()
                if not row:
                    return False
                new_val = row[0] + delta
                if new_val < 0:
                    return False
                cur.execute("UPDATE blood_stock SET units_available=%s WHERE blood_group=%s", (new_val, blood_group))
                conn.commit()
                return True
        except Error:
            logger.exception("Update stock failed")
            return False
