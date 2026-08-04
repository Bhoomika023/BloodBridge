"""Request service for emergency coordination requests."""
import logging
from datetime import date

from database.db_connection import get_connection
from mysql.connector import Error
from services.stock_service import StockService
from services.validation import normalize_blood_group, require_text, validate_phone_number, validate_units


logger = logging.getLogger(__name__)


class RequestService:
    @staticmethod
    def create_emergency_request(
        patient_name,
        blood_group,
        units_needed,
        hospital_name,
        city,
        urgency_level,
        contact_number,
        district="Mysuru",
        state="Karnataka",
    ):
        """Create a request and raise an alert when city stock cannot cover it.

        Stock is not deducted here because a request is not a confirmed
        donation or dispatch. Stock should be reduced only when blood is
        actually arranged/issued, avoiding false inventory loss for cancelled
        or unresolved emergency requests.
        """
        patient_name = require_text(patient_name, "patient name")
        blood_group = normalize_blood_group(blood_group)
        units_needed = validate_units(units_needed, minimum=1, maximum=20)
        hospital_name = require_text(hospital_name, "hospital name")
        city = require_text(city, "city")
        urgency_level = require_text(urgency_level, "urgency level")
        contact_number = validate_phone_number(contact_number)
        priority = urgency_level.title()
        available_units = StockService.get_units_for_city(city, blood_group)
        stock_shortage = available_units < units_needed
        if stock_shortage:
            priority = "Critical"
        alert_id = None
        try:
            with get_connection() as conn:
                cur = conn.cursor()
                cur.execute(
                    """
                    INSERT INTO blood_request
                    (patient_name, blood_group, units_needed, hospital_name, city, district, state, request_date, created_time, status, priority, contact_number)
                    VALUES (%s,%s,%s,%s,%s,%s,%s,%s,NOW(),'Active',%s,%s)
                    """,
                    (patient_name, blood_group, units_needed, hospital_name, city, district, state, date.today(), priority, contact_number),
                )
                request_id = cur.lastrowid
                if stock_shortage:
                    alert_urgency = "CRITICAL"
                    cur.execute(
                    """
                    INSERT INTO emergency_alerts
                    (request_id, patient_name, blood_group, city, district, state, hospital_name, urgency_level, required_units, request_time, status)
                    VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,NOW(),'OPEN')
                    """,
                        (request_id, patient_name, blood_group, city, district, state, hospital_name, alert_urgency, units_needed),
                    )
                    alert_id = cur.lastrowid
                conn.commit()
                return {
                    "request_id": request_id,
                    "alert_id": alert_id,
                    "available_units": available_units,
                    "stock_shortage": stock_shortage,
                }
        except Error:
            logger.exception("Create emergency request failed")
            return None

    @staticmethod
    def get_active_requests():
        sql = """
        SELECT request_id, patient_name, blood_group, units_needed, hospital_name, city, district, state, request_date, created_time, status, priority, contact_number
        FROM blood_request
        WHERE status='Active'
        ORDER BY FIELD(priority,'Critical','High','Normal'), created_time DESC, request_id DESC
        """
        try:
            with get_connection() as conn:
                cur = conn.cursor()
                cur.execute(sql)
                return cur.fetchall()
        except Error:
            logger.exception("Get active requests failed")
            return []

    @staticmethod
    def resolve_request(request_id):
        try:
            with get_connection() as conn:
                cur = conn.cursor()
                cur.execute("UPDATE blood_request SET status='Resolved' WHERE request_id=%s AND status='Active'", (request_id,))
                if cur.rowcount == 0:
                    logger.warning("Resolve request skipped for missing or inactive request_id=%s", request_id)
                    return False
                cur.execute(
                    """
                    UPDATE emergency_alerts
                    SET status='FULFILLED'
                    WHERE request_id=%s
                      AND status IN ('OPEN','CONTACTING_DONORS')
                    """,
                    (request_id,),
                )
                conn.commit()
                return True
        except Error:
            logger.exception("Resolve request failed")
            return False

    @staticmethod
    def get_resolved_requests(limit=100):
        sql = """
        SELECT request_id, patient_name, blood_group, units_needed, hospital_name, city, district, state, request_date, created_time, status, priority, contact_number
        FROM blood_request
        WHERE status='Resolved'
        ORDER BY created_time DESC, request_id DESC
        LIMIT %s
        """
        try:
            with get_connection() as conn:
                cur = conn.cursor()
                cur.execute(sql, (validate_units(limit, minimum=1, maximum=1000),))
                return cur.fetchall()
        except Error:
            logger.exception("Get resolved requests failed")
            return []

    @staticmethod
    def get_pending_requests():
        """Backward-compatible alias for existing dashboard integrations."""
        return RequestService.get_active_requests()
