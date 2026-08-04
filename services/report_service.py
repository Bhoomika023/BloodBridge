"""
Report service demonstrating aggregate functions and joins.
"""
from database.db_connection import get_connection


class ReportService:
    @staticmethod
    def total_donors():
        sql = "SELECT COUNT(*) FROM donor"
        with get_connection() as conn:
            cur = conn.cursor()
            cur.execute(sql)
            return cur.fetchone()[0]

    @staticmethod
    def total_units():
        sql = "SELECT SUM(units_available) FROM city_stock"
        with get_connection() as conn:
            cur = conn.cursor()
            cur.execute(sql)
            return cur.fetchone()[0] or 0

    @staticmethod
    def dashboard_stats():
        queries = {
            "total_donors": "SELECT COUNT(*) FROM donor",
            "total_units": "SELECT COALESCE(SUM(units_available),0) FROM city_stock",
            "emergency_requests": "SELECT COUNT(*) FROM blood_request WHERE priority IN ('High','Critical') AND status='Active'",
            "critical_alerts": "SELECT COUNT(*) FROM emergency_alerts WHERE urgency_level='CRITICAL' AND status='OPEN'",
            "available_cities": "SELECT COUNT(DISTINCT city) FROM city_stock",
            "active_donors": "SELECT COUNT(*) FROM donor WHERE availability_status='Available'",
        }
        stats = {}
        with get_connection() as conn:
            cur = conn.cursor()
            for key, sql in queries.items():
                cur.execute(sql)
                stats[key] = cur.fetchone()[0] or 0
        return stats

    @staticmethod
    def most_requested_blood_group():
        sql = "SELECT blood_group, COUNT(*) as cnt FROM blood_request GROUP BY blood_group ORDER BY cnt DESC LIMIT 1"
        with get_connection() as conn:
            cur = conn.cursor()
            cur.execute(sql)
            row = cur.fetchone()
            return row if row else (None, 0)

    @staticmethod
    def monthly_donations():
        # aggregate by year-month to be ONLY_FULL_GROUP_BY safe
        sql = """
        SELECT DATE_FORMAT(donation_date, '%%Y-%%m') AS month_key,
               DATE_FORMAT(donation_date, '%%b %%Y') AS month_label,
               COUNT(*) AS donations,
               COALESCE(SUM(units_donated),0) AS units
        FROM donation_history
        WHERE donation_date IS NOT NULL
        GROUP BY month_key, month_label
        ORDER BY month_key
        """
        with get_connection() as conn:
            cur = conn.cursor()
            cur.execute(sql)
            return cur.fetchall()

    @staticmethod
    def top_donor_cities():
        sql = """
        SELECT d.city AS city,
               COUNT(*) AS total_donors
        FROM donor d
        GROUP BY d.city
        ORDER BY total_donors DESC, city
        """
        with get_connection() as conn:
            cur = conn.cursor()
            cur.execute(sql)
            return cur.fetchall()

    @staticmethod
    def requests_by_blood_group():
        sql = """
        SELECT blood_group, COUNT(*) AS requests
        FROM blood_request
        GROUP BY blood_group
        ORDER BY requests DESC, blood_group
        """
        with get_connection() as conn:
            cur = conn.cursor()
            cur.execute(sql)
            return cur.fetchall()

    @staticmethod
    def most_requested_blood_groups():
        sql = """
        SELECT blood_group, COALESCE(SUM(units_needed),0) AS units_requested
        FROM blood_request
        GROUP BY blood_group
        ORDER BY units_requested DESC, blood_group
        """
        with get_connection() as conn:
            cur = conn.cursor()
            cur.execute(sql)
            return cur.fetchall()

    @staticmethod
    def most_available_blood_groups():
        sql = """
        SELECT blood_group, COALESCE(SUM(units_available),0) AS units_available
        FROM city_stock
        GROUP BY blood_group
        ORDER BY units_available DESC, blood_group
        """
        with get_connection() as conn:
            cur = conn.cursor()
            cur.execute(sql)
            return cur.fetchall()

    @staticmethod
    def blood_demand_vs_supply():
        sql = """
        SELECT b.blood_group,
               COALESCE(r.requested_units, 0) AS requested_units,
               COALESCE(s.available_units, 0) AS available_units
        FROM (
            SELECT DISTINCT blood_group FROM blood_request
            UNION
            SELECT DISTINCT blood_group FROM city_stock
        ) b
        LEFT JOIN (
            SELECT blood_group, COALESCE(SUM(units_needed),0) AS requested_units
            FROM blood_request
            GROUP BY blood_group
        ) r ON r.blood_group = b.blood_group
        LEFT JOIN (
            SELECT blood_group, COALESCE(SUM(units_available),0) AS available_units
            FROM city_stock
            GROUP BY blood_group
        ) s ON s.blood_group = b.blood_group
        ORDER BY requested_units DESC, b.blood_group
        """
        with get_connection() as conn:
            cur = conn.cursor()
            cur.execute(sql)
            return cur.fetchall()

    @staticmethod
    def emergency_response_success_rate():
        sql = """
        SELECT status, COUNT(*) AS total
        FROM blood_request
        GROUP BY status
        ORDER BY FIELD(status, 'Resolved', 'Active')
        """
        with get_connection() as conn:
            cur = conn.cursor()
            cur.execute(sql)
            return cur.fetchall()

    @staticmethod
    def city_ranking():
        sql = """
        SELECT d.city,
               COUNT(*) AS donors,
               COALESCE((SELECT SUM(units_available) FROM city_stock s WHERE s.city = d.city), 0) AS stock_units
        FROM donor d
        GROUP BY d.city
        ORDER BY donors DESC, stock_units DESC, d.city
        """
        with get_connection() as conn:
            cur = conn.cursor()
            cur.execute(sql)
            return cur.fetchall()

    @staticmethod
    def city_wise_donations():
        # Return total donors per city (ONLY_FULL_GROUP_BY safe)
        sql = """
        SELECT d.city AS city,
               COUNT(*) AS total_donors
        FROM donor d
        GROUP BY d.city
        ORDER BY total_donors DESC
        """
        with get_connection() as conn:
            cur = conn.cursor()
            cur.execute(sql)
            return cur.fetchall()

    @staticmethod
    def blood_group_demand():
        # Count requests per blood group and sum units requested. Also compute available units from city_stock per group.
        sql = """
        SELECT r.blood_group AS blood_group,
               COUNT(*) AS total_requests,
               COALESCE(SUM(r.units_needed),0) AS units_requested
        FROM blood_request r
        WHERE r.city IN (SELECT DISTINCT city FROM city_stock)
        GROUP BY r.blood_group
        ORDER BY units_requested DESC
        """
        with get_connection() as conn:
            cur = conn.cursor()
            cur.execute(sql)
            return cur.fetchall()

    @staticmethod
    def blood_group_distribution():
        sql = """
        SELECT blood_group, COUNT(*) AS donors
        FROM donor
        GROUP BY blood_group
        ORDER BY donors DESC, blood_group
        """
        with get_connection() as conn:
            cur = conn.cursor()
            cur.execute(sql)
            return cur.fetchall()

    @staticmethod
    def emergency_trends():
        sql = """
        SELECT urgency_level, COUNT(*) AS count
        FROM emergency_alerts
        GROUP BY urgency_level
        ORDER BY FIELD(urgency_level,'CRITICAL','HIGH','NORMAL')
        """
        with get_connection() as conn:
            cur = conn.cursor()
            cur.execute(sql)
            return cur.fetchall()

    @staticmethod
    def monthly_request_trends():
        # Aggregate requests by year-month; alias used in GROUP BY for ONLY_FULL_GROUP_BY compatibility
        sql = """
        SELECT DATE_FORMAT(created_time, '%%Y-%%m') AS month_key,
               DATE_FORMAT(created_time, '%%b %%Y') AS month_label,
               COUNT(*) AS requests
        FROM blood_request
        WHERE created_time IS NOT NULL
        GROUP BY month_key, month_label
        ORDER BY month_key
        """
        with get_connection() as conn:
            cur = conn.cursor()
            cur.execute(sql)
            return cur.fetchall()

    @staticmethod
    def low_stock_analysis(threshold=2):
        sql = """
        SELECT city, blood_group, units_available AS units
        FROM city_stock
        WHERE units_available <= %s
        ORDER BY units_available ASC, city
        """
        with get_connection() as conn:
            cur = conn.cursor()
            cur.execute(sql, (threshold,))
            return cur.fetchall()
