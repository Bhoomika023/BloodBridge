"""Runtime database upgrade helpers for the emergency network schema."""
import logging

from database.db_connection import get_connection


logger = logging.getLogger(__name__)


class SetupService:
    @staticmethod
    def ensure_emergency_schema():
        with get_connection() as conn:
            cur = conn.cursor()
            SetupService._create_core_tables(cur)
            SetupService._ensure_donor_columns(cur)
            SetupService._ensure_request_columns(cur)
            SetupService._ensure_donation_columns(cur)
            SetupService._create_emergency_tables(cur)
            SetupService._ensure_indexes(cur)
            SetupService._seed_emergency_data(cur)
            conn.commit()

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
    def _table_is_empty(cur, table_name):
        cur.execute(f"SELECT COUNT(*) FROM {table_name}")
        return cur.fetchone()[0] == 0

    @staticmethod
    def _index_exists(cur, table_name, index_name):
        cur.execute(
            """
            SELECT COUNT(*)
            FROM information_schema.statistics
            WHERE table_schema = DATABASE() AND table_name=%s AND index_name=%s
            """,
            (table_name, index_name),
        )
        return cur.fetchone()[0] > 0

    @staticmethod
    def _constraint_exists(cur, table_name, constraint_name):
        cur.execute(
            """
            SELECT COUNT(*)
            FROM information_schema.table_constraints
            WHERE table_schema = DATABASE() AND table_name=%s AND constraint_name=%s
            """,
            (table_name, constraint_name),
        )
        return cur.fetchone()[0] > 0

    @staticmethod
    def _create_core_tables(cur):
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS donor (
              donor_id INT PRIMARY KEY AUTO_INCREMENT,
              full_name VARCHAR(150) NOT NULL,
              age INT NOT NULL,
              gender ENUM('Male','Female','Other') NOT NULL,
              blood_group VARCHAR(5) NOT NULL,
              city VARCHAR(100) NOT NULL,
              district VARCHAR(100),
              state VARCHAR(100) NOT NULL DEFAULT 'Karnataka',
              availability_status ENUM('Available','Recently Donated','Inactive') NOT NULL DEFAULT 'Available',
              contact_number VARCHAR(20) UNIQUE NOT NULL,
              email VARCHAR(100) UNIQUE,
              last_donation_date DATE
            )
            """
        )
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS blood_request (
              request_id INT PRIMARY KEY AUTO_INCREMENT,
              patient_name VARCHAR(150) NOT NULL,
              blood_group VARCHAR(5) NOT NULL,
              units_needed INT NOT NULL,
              hospital_name VARCHAR(150) NOT NULL,
              city VARCHAR(100) NOT NULL,
              district VARCHAR(100) NOT NULL DEFAULT 'Mysuru',
              state VARCHAR(100) NOT NULL DEFAULT 'Karnataka',
              request_date DATE NOT NULL,
              created_time DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
              status ENUM('Active','Resolved') NOT NULL DEFAULT 'Active',
              priority ENUM('Normal','High','Critical') NOT NULL DEFAULT 'Normal',
              contact_number VARCHAR(15) NOT NULL DEFAULT ''
            )
            """
        )
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS donation_history (
              donation_id INT PRIMARY KEY AUTO_INCREMENT,
              donor_id INT NOT NULL,
              donation_date DATE NOT NULL,
              units_donated INT NOT NULL,
                            hospital_name VARCHAR(150) NULL,
              FOREIGN KEY (donor_id) REFERENCES donor(donor_id) ON DELETE CASCADE
            )
            """
        )

    @staticmethod
    def _ensure_donor_columns(cur):
        if not SetupService._column_exists(cur, "donor", "district"):
            cur.execute("ALTER TABLE donor ADD COLUMN district VARCHAR(100) AFTER city")
        if not SetupService._column_exists(cur, "donor", "state"):
            cur.execute("ALTER TABLE donor ADD COLUMN state VARCHAR(100) NOT NULL DEFAULT 'Karnataka' AFTER district")
        if not SetupService._column_exists(cur, "donor", "availability_status"):
            cur.execute(
                "ALTER TABLE donor ADD COLUMN availability_status "
                "ENUM('Available','Recently Donated','Inactive') NOT NULL DEFAULT 'Available' AFTER state"
            )
        if not SetupService._column_exists(cur, "donor", "contact_number"):
            cur.execute("ALTER TABLE donor ADD COLUMN contact_number VARCHAR(20) AFTER availability_status")
        if SetupService._column_exists(cur, "donor", "phone"):
            cur.execute("UPDATE donor SET contact_number = phone WHERE contact_number IS NULL AND phone IS NOT NULL")
        cur.execute("UPDATE donor SET contact_number = CONCAT('AUTO', donor_id) WHERE contact_number IS NULL")

    @staticmethod
    def _ensure_request_columns(cur):
        if not SetupService._column_exists(cur, "blood_request", "city"):
            cur.execute("ALTER TABLE blood_request ADD COLUMN city VARCHAR(100) NOT NULL DEFAULT 'Mysore' AFTER hospital_name")
        if not SetupService._column_exists(cur, "blood_request", "district"):
            cur.execute("ALTER TABLE blood_request ADD COLUMN district VARCHAR(100) NOT NULL DEFAULT 'Mysuru' AFTER city")
        if not SetupService._column_exists(cur, "blood_request", "state"):
            cur.execute("ALTER TABLE blood_request ADD COLUMN state VARCHAR(100) NOT NULL DEFAULT 'Karnataka' AFTER district")
        if not SetupService._column_exists(cur, "blood_request", "created_time"):
            cur.execute("ALTER TABLE blood_request ADD COLUMN created_time DATETIME NULL AFTER request_date")
            cur.execute("UPDATE blood_request SET created_time = CONCAT(request_date, ' 09:00:00') WHERE created_time IS NULL")
            cur.execute("ALTER TABLE blood_request MODIFY created_time DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP")
        if not SetupService._column_exists(cur, "blood_request", "priority"):
            cur.execute("ALTER TABLE blood_request ADD COLUMN priority ENUM('Normal','High','Critical') NOT NULL DEFAULT 'Normal' AFTER status")
        if not SetupService._column_exists(cur, "blood_request", "contact_number"):
            cur.execute("ALTER TABLE blood_request ADD COLUMN contact_number VARCHAR(15) NOT NULL DEFAULT '' AFTER priority")
        cur.execute("UPDATE blood_request SET status='Resolved' WHERE status IN ('Approved','Rejected')")
        cur.execute("UPDATE blood_request SET status='Active' WHERE status IN ('Pending','Escalated')")
        cur.execute("ALTER TABLE blood_request MODIFY status ENUM('Active','Resolved') NOT NULL DEFAULT 'Active'")

    @staticmethod
    def _ensure_donation_columns(cur):
        if not SetupService._column_exists(cur, "donation_history", "hospital_name"):
            cur.execute("ALTER TABLE donation_history ADD COLUMN hospital_name VARCHAR(150) NULL AFTER units_donated")

    @staticmethod
    def _create_emergency_tables(cur):
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS hospitals (
              hospital_id INT PRIMARY KEY AUTO_INCREMENT,
              hospital_name VARCHAR(150) NOT NULL,
              city VARCHAR(100) NOT NULL,
              district VARCHAR(100) NOT NULL DEFAULT 'Mysuru',
              state VARCHAR(100) NOT NULL DEFAULT 'Karnataka',
              emergency_contact VARCHAR(20) NOT NULL
            )
            """
        )
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS city_stock (
              stock_id INT PRIMARY KEY AUTO_INCREMENT,
              city VARCHAR(100) NOT NULL,
              district VARCHAR(100) NOT NULL DEFAULT 'Mysuru',
              state VARCHAR(100) NOT NULL DEFAULT 'Karnataka',
              blood_group VARCHAR(5) NOT NULL,
              units_available INT NOT NULL DEFAULT 0,
              UNIQUE KEY unique_city_blood (city, blood_group)
            )
            """
        )
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS emergency_alerts (
              alert_id INT PRIMARY KEY AUTO_INCREMENT,
              request_id INT NULL,
              patient_name VARCHAR(150) NOT NULL,
              blood_group VARCHAR(5) NOT NULL,
              city VARCHAR(100) NOT NULL,
              district VARCHAR(100) NOT NULL DEFAULT 'Mysuru',
              state VARCHAR(100) NOT NULL DEFAULT 'Karnataka',
              hospital_name VARCHAR(150) NOT NULL,
              urgency_level ENUM('NORMAL','HIGH','CRITICAL') NOT NULL DEFAULT 'NORMAL',
              required_units INT NOT NULL,
              request_time DATETIME NOT NULL,
              status ENUM('OPEN','CONTACTING_DONORS','FULFILLED','CLOSED') NOT NULL DEFAULT 'OPEN',
              CONSTRAINT fk_emergency_alert_request
                FOREIGN KEY (request_id) REFERENCES blood_request(request_id)
                ON DELETE SET NULL
            )
            """
        )
        if not SetupService._column_exists(cur, "emergency_alerts", "request_id"):
            cur.execute("ALTER TABLE emergency_alerts ADD COLUMN request_id INT NULL AFTER alert_id")
        if not SetupService._constraint_exists(cur, "emergency_alerts", "fk_emergency_alert_request"):
            cur.execute(
                """
                ALTER TABLE emergency_alerts
                ADD CONSTRAINT fk_emergency_alert_request
                FOREIGN KEY (request_id) REFERENCES blood_request(request_id)
                ON DELETE SET NULL
                """
            )
        for table in ("city_stock", "hospitals", "emergency_alerts"):
            for column, ddl in (
                ("district", f"ALTER TABLE {table} ADD COLUMN district VARCHAR(100) NOT NULL DEFAULT 'Mysuru' AFTER city"),
                ("state", f"ALTER TABLE {table} ADD COLUMN state VARCHAR(100) NOT NULL DEFAULT 'Karnataka' AFTER district"),
            ):
                if not SetupService._column_exists(cur, table, column):
                    cur.execute(ddl)

    @staticmethod
    def _ensure_indexes(cur):
        indexes = (
            ("donor", "idx_donor_match", "CREATE INDEX idx_donor_match ON donor (blood_group, city, availability_status)"),
            ("blood_request", "idx_request_queue", "CREATE INDEX idx_request_queue ON blood_request (status, priority, created_time)"),
            ("emergency_alerts", "idx_alert_queue", "CREATE INDEX idx_alert_queue ON emergency_alerts (status, urgency_level, request_time)"),
        )
        for table, index_name, ddl in indexes:
            if not SetupService._index_exists(cur, table, index_name):
                cur.execute(ddl)

    @staticmethod
    def _seed_emergency_data(cur):
        if SetupService._table_is_empty(cur, "hospitals"):
            cur.executemany(
                """
                INSERT IGNORE INTO hospitals (hospital_name, city, district, state, emergency_contact)
                VALUES (%s,%s,%s,%s,%s)
                """,
                [
                    ("Apollo Hospital", "Mysore", "Mysuru", "Karnataka", "0821123456"),
                    ("JSS Hospital", "Mysore", "Mysuru", "Karnataka", "0821654321"),
                    ("Manipal Hospital", "Bangalore", "Bengaluru Urban", "Karnataka", "0802233445"),
                    ("City Care Hospital", "Mangalore", "Dakshina Kannada", "Karnataka", "0824223344"),
                    ("KIMS Emergency", "Hubli", "Dharwad", "Karnataka", "0836221100"),
                ],
            )
        if SetupService._table_is_empty(cur, "city_stock"):
            cur.executemany(
                """
                INSERT IGNORE INTO city_stock (city, district, state, blood_group, units_available)
                VALUES (%s,%s,%s,%s,%s)
                """,
                [
                    ("Mysore", "Mysuru", "Karnataka", "A+", 12),
                    ("Mysore", "Mysuru", "Karnataka", "O+", 8),
                    ("Mysore", "Mysuru", "Karnataka", "O-", 1),
                    ("Mysore", "Mysuru", "Karnataka", "B+", 6),
                    ("Bangalore", "Bengaluru Urban", "Karnataka", "AB+", 20),
                    ("Bangalore", "Bengaluru Urban", "Karnataka", "O-", 4),
                    ("Mangalore", "Dakshina Kannada", "Karnataka", "O-", 2),
                    ("Hubli", "Dharwad", "Karnataka", "B-", 2),
                ],
            )
        donor_columns = [
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
        donor_rows = [
            ("Arjun Rao", 29, "Male", "O-", "Mysore", "Mysuru", "Karnataka", "Available", "9000010001", "arjun.rao@example.com", "2026-01-12"),
            ("Nisha Gowda", 34, "Female", "O-", "Mysore", "Mysuru", "Karnataka", "Available", "9000010002", "nisha.gowda@example.com", "2025-12-08"),
            ("Vikram Hegde", 41, "Male", "O-", "Mysore", "Mysuru", "Karnataka", "Recently Donated", "9000010003", "vikram.hegde@example.com", None),
            ("Farah Khan", 37, "Female", "O-", "Mangalore", "Dakshina Kannada", "Karnataka", "Available", "9000010008", "farah.khan@example.com", "2026-01-21"),
        ]
        if SetupService._table_is_empty(cur, "donor"):
            if SetupService._column_exists(cur, "donor", "phone"):
                donor_columns.insert(9, "phone")
                donor_rows = [row[:9] + (row[8],) + row[9:] for row in donor_rows]
            placeholders = ",".join(["%s"] * len(donor_columns))
            cur.executemany(
                f"INSERT IGNORE INTO donor ({','.join(donor_columns)}) VALUES ({placeholders})",
                donor_rows,
            )
        if SetupService._table_is_empty(cur, "donation_history"):
            cur.execute(
                """
                INSERT INTO donation_history (donor_id, donation_date, units_donated, hospital_name)
                SELECT donor_id, '2026-01-12', 1, 'Apollo Hospital' FROM donor
                WHERE contact_number='9000010001'
                """
            )
            cur.execute(
                """
                INSERT INTO donation_history (donor_id, donation_date, units_donated, hospital_name)
                SELECT donor_id, '2025-12-08', 1, 'JSS Hospital' FROM donor
                WHERE contact_number='9000010002'
                """
            )
