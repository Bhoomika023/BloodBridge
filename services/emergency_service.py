"""Emergency coordination service for alert creation and donor matching."""
import logging
from datetime import date

from database.db_connection import get_connection
from mysql.connector import Error
from services.donor_service import DonorService
from services.stock_service import StockService
from services.validation import normalize_blood_group, require_text, validate_phone_number, validate_units


logger = logging.getLogger(__name__)


class EmergencyService:
    @staticmethod
    def create_alert(patient_name, blood_group, city, hospital_name, urgency_level, required_units, contact_number="", district="Mysuru", state="Karnataka"):
        patient_name = require_text(patient_name, "patient name")
        blood_group = normalize_blood_group(blood_group)
        city = require_text(city, "city")
        hospital_name = require_text(hospital_name, "hospital name")
        urgency = require_text(urgency_level, "urgency level").upper()
        required_units = validate_units(required_units, minimum=1, maximum=20)
        contact_number = validate_phone_number(contact_number) if contact_number else ""
        sql_request = """
        INSERT INTO blood_request
        (patient_name, blood_group, units_needed, hospital_name, city, district, state, request_date, created_time, status, priority, contact_number)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,NOW(),'Active',%s,%s)
        """
        sql_alert = """
        INSERT INTO emergency_alerts
        (request_id, patient_name, blood_group, city, district, state, hospital_name, urgency_level, required_units, request_time, status)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,NOW(),'OPEN')
        """
        try:
            with get_connection() as conn:
                cur = conn.cursor()
                cur.execute(
                    sql_request,
                    (patient_name, blood_group, required_units, hospital_name, city, district, state, date.today(), urgency.title(), contact_number),
                )
                request_id = cur.lastrowid
                cur.execute(
                    sql_alert,
                    (request_id, patient_name, blood_group, city, district, state, hospital_name, urgency, required_units),
                )
                alert_id = cur.lastrowid
                conn.commit()
                return alert_id
        except Error:
            logger.exception("Create alert failed")
            return None

    @staticmethod
    def get_alerts(status=None, limit=20):
        sql = """
         SELECT alert_id, patient_name, blood_group, city, district, state, hospital_name, urgency_level,
             required_units, request_time, status, request_id
        FROM emergency_alerts
        """
        params = []
        if status:
            sql += " WHERE status=%s"
            params.append(status)
        sql += """
        ORDER BY FIELD(urgency_level, 'CRITICAL','HIGH','NORMAL'), request_time DESC
        LIMIT %s
        """
        params.append(limit)
        try:
            with get_connection() as conn:
                cur = conn.cursor()
                cur.execute(sql, tuple(params))
                return cur.fetchall()
        except Error:
            logger.exception("Get alerts failed")
            return []

    @staticmethod
    def active_high_alert():
        alerts = EmergencyService.get_alerts(status="OPEN", limit=1)
        if not alerts:
            return None
        alert = alerts[0]
        available = StockService.get_units_for_city(alert[3], alert[2])
        matches = DonorService.find_matching_donors(alert[2], alert[3])
        return {
            "alert_id": alert[0],
            "patient_name": alert[1],
            "blood_group": alert[2],
            "city": alert[3],
            "district": alert[4],
            "state": alert[5],
            "hospital_name": alert[6],
            "urgency_level": alert[7],
            "required_units": alert[8],
            "request_time": alert[9],
            "status": alert[10],
            "request_id": alert[11],
            "available_units": available,
            "matching_donors": matches,
        }

    @staticmethod
    def mark_alert_fulfilled(alert_id):
        try:
            with get_connection() as conn:
                cur = conn.cursor()
                cur.execute(
                    """
                    SELECT request_id
                    FROM emergency_alerts
                    WHERE alert_id=%s AND status IN ('OPEN','CONTACTING_DONORS')
                    """,
                    (alert_id,),
                )
                row = cur.fetchone()
                if not row or not row[0]:
                    return False

                request_id = row[0]
                cur.execute("UPDATE emergency_alerts SET status='FULFILLED' WHERE alert_id=%s", (alert_id,))
                cur.execute(
                    """
                    UPDATE blood_request
                    SET status='Resolved'
                    WHERE request_id=%s AND status='Active'
                    """,
                    (request_id,),
                )
                conn.commit()
                return True
        except Error:
            logger.exception("Mark alert fulfilled failed")
            return False

    @staticmethod
    def smart_search(city=None, blood_group=None, donor_name=None, hospital=None, urgency=None):
        results = {"donors": [], "requests": [], "alerts": []}
        results["donors"] = DonorService.search_donors(
            name=donor_name,
            blood_group=blood_group,
            city=city,
            status="Available" if not donor_name else None,
        )
        request_sql = """
        SELECT request_id, patient_name, hospital_name, city, blood_group, units_needed, priority, status, contact_number
        FROM blood_request WHERE 1=1
        """
        alert_sql = """
        SELECT alert_id, patient_name, hospital_name, city, blood_group, required_units, urgency_level, status
        FROM emergency_alerts WHERE 1=1
        """
        params = []
        alert_params = []
        city = city.strip() if city else None
        blood_group = normalize_blood_group(blood_group) if blood_group else None
        hospital = hospital.strip() if hospital else None
        request_filters = (
            (city, " AND city LIKE %s", f"%{city}%" if city else None),
            (blood_group, " AND blood_group=%s", blood_group),
            (hospital, " AND hospital_name LIKE %s", f"%{hospital}%" if hospital else None),
            (urgency, " AND priority=%s", urgency.title() if urgency else None),
        )
        alert_filters = (
            (city, " AND city LIKE %s", f"%{city}%" if city else None),
            (blood_group, " AND blood_group=%s", blood_group),
            (hospital, " AND hospital_name LIKE %s", f"%{hospital}%" if hospital else None),
            (urgency, " AND urgency_level=%s", urgency.upper() if urgency else None),
        )
        for value, clause, param in request_filters:
            if value:
                request_sql += clause
                params.append(param)
        for value, clause, param in alert_filters:
            if value:
                alert_sql += clause
                alert_params.append(param)
        request_sql += " ORDER BY FIELD(priority,'Critical','High','Normal'), request_date DESC"
        alert_sql += " ORDER BY FIELD(urgency_level,'CRITICAL','HIGH','NORMAL'), request_time DESC"
        try:
            with get_connection() as conn:
                cur = conn.cursor()
                cur.execute(request_sql, tuple(params))
                results["requests"] = cur.fetchall()
                cur.execute(alert_sql, tuple(alert_params))
                results["alerts"] = cur.fetchall()
        except Error:
            logger.exception("Smart search failed")
        return results
