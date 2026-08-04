"""
Comprehensive database seeder for demo/viva.

Usage (from workspace root):
    cd CrimsonLife
    python -m database.seed_database

This script ensures:
- Each city has multiple `city_stock` entries (multiple blood groups)
- Each city has at least `MIN_PER_CITY` donors (inserts only if fewer exist)
- Some cities intentionally have low/critical stock for O- or AB-
- Avoids duplicate contacts/emails
"""
from datetime import date, datetime, timedelta
import logging
import random

from database.db_connection import get_connection
from services.donor_service import DonorService
from models.donor_model import Donor
from mysql.connector import Error
from services.validation import normalize_blood_group


MIN_PER_CITY = 7
logger = logging.getLogger(__name__)

# ensure these cities are covered in demo
REQUIRED_CITIES = [
    ("Mysore", "Mysuru", "Karnataka"),
    ("Bangalore", "Bengaluru Urban", "Karnataka"),
    ("Mangalore", "Dakshina Kannada", "Karnataka"),
    ("Hubli", "Dharwad", "Karnataka"),
    ("Belagavi", "Belagavi", "Karnataka"),
    ("Tumkur", "Tumakuru", "Karnataka"),
    ("Shivamogga", "Shimoga", "Karnataka"),
]

BLOOD_GROUPS = ["A+", "B+", "O+", "O-", "AB+", "AB-", "A-", "B-"]

HOSPITALS = [
    ("Apollo Hospital", "Mysore", "Mysuru", "Karnataka", "0821123456"),
    ("JSS Hospital", "Mysore", "Mysuru", "Karnataka", "0821654321"),
    ("K.R. Hospital", "Mysore", "Mysuru", "Karnataka", "0821244788"),
    ("Manipal Hospital", "Bangalore", "Bengaluru Urban", "Karnataka", "0802233445"),
    ("St. John’s Medical College Hospital", "Bangalore", "Bengaluru Urban", "Karnataka", "0802212345"),
    ("Ramaiah Memorial Hospital", "Bangalore", "Bengaluru Urban", "Karnataka", "08023671234"),
    ("City Care Hospital", "Mangalore", "Dakshina Kannada", "Karnataka", "0824223344"),
    ("A.J. Hospital", "Mangalore", "Dakshina Kannada", "Karnataka", "0824229988"),
    ("KIMS Emergency", "Hubli", "Dharwad", "Karnataka", "0836221100"),
    ("SDM Medical College Hospital", "Hubli", "Dharwad", "Karnataka", "0836223344"),
    ("Belagavi Institute of Medical Sciences", "Belagavi", "Belagavi", "Karnataka", "0831422334"),
    ("Tumakuru District Hospital", "Tumkur", "Tumakuru", "Karnataka", "0816221144"),
    ("Nanjappa Hospital", "Shivamogga", "Shimoga", "Karnataka", "0818223344"),
]

NAMES = [
    "Rahul Sharma", "Priya Nair", "Arjun Reddy", "Sneha Kulkarni", "Karthik Rao", "Ananya Das",
    "Rohit Verma", "Sana Iyer", "Vikram Singh", "Meera Menon", "Kavya Patel", "Amit Joshi",
    "Nikhil Bhat", "Isha Rao", "Siddharth Rao", "Divya Nair", "Arpita Sen", "Manish Gupta",
    "Pooja Shah", "Suresh Naik", "Leela Shetty", "Asha Prasad", "Dinesh Kumar", "Rekha Reddy",
]


def _rand_age():
    return random.randint(18, 60)


def _rand_gender():
    return random.choices(["Male", "Female", "Other"], weights=[48, 48, 4])[0]


def _unique_phone(existing):
    prefixes = ["9", "8", "7"]
    for _ in range(500):
        num = random.choice(prefixes) + "".join(str(random.randint(0, 9)) for _ in range(9))
        if num not in existing:
            existing.add(num)
            return num
    raise RuntimeError("Could not generate unique phone number")


def _make_email(name, phone):
    clean = name.lower().replace(" ", ".")
    return f"{clean}.{phone[-4:]}@example.com"


def _random_datetime(days_back=75):
    days = random.randint(0, days_back)
    hours = random.randint(0, 23)
    minutes = random.randint(0, 59)
    return datetime.now() - timedelta(days=days, hours=hours, minutes=minutes)


def ensure_hospitals(cur):
    cur.executemany(
        """
        INSERT IGNORE INTO hospitals (hospital_name, city, district, state, emergency_contact)
        VALUES (%s,%s,%s,%s,%s)
        """,
        HOSPITALS,
    )


def ensure_city_stock(cur, city, district, state):
    # Insert demo stock only when a city/blood-group row does not already exist.
    # This keeps the command non-destructive for production or previously seeded data.
    base = {
        "A+": random.randint(5, 20),
        "B+": random.randint(5, 18),
        "O+": random.randint(8, 25),
        "O-": random.randint(0, 6),
        "AB+": random.randint(2, 12),
        "AB-": random.randint(0, 4),
        "A-": random.randint(0, 6),
        "B-": random.randint(0, 6),
    }

    # force some critical shortages for demo clarity
    low_cities = {"Hubli": "O-", "Belagavi": "O-", "Tumkur": "AB-"}
    if city in low_cities:
        grp = low_cities[city]
        base[grp] = random.randint(0, 1)

    # ensure Bangalore is well stocked
    if city.lower().startswith("bangalore") or city.lower().startswith("bengaluru"):
        for g in base:
            base[g] = max(base[g], random.randint(10, 30))

    for bg, units in base.items():
        cur.execute(
            "SELECT COUNT(*) FROM city_stock WHERE city=%s AND blood_group=%s",
            (city, bg),
        )
        if cur.fetchone()[0] == 0:
            cur.execute(
                "INSERT INTO city_stock (city, district, state, blood_group, units_available) VALUES (%s,%s,%s,%s,%s)",
                (city, district, state, bg, units),
            )


def _hospital_rows_for_city(city):
    matches = [row for row in HOSPITALS if row[1] == city]
    return matches or HOSPITALS


def seed_requests(cur, target_count=20):
    cur.execute("SELECT COUNT(*) FROM blood_request")
    existing_count = cur.fetchone()[0]
    needed = max(0, target_count - existing_count)
    if needed == 0:
        return

    cur.execute("SELECT city, district, state FROM city_stock GROUP BY city, district, state")
    cities = cur.fetchall()
    cur.execute("SELECT donor_id, full_name, city, district, state FROM donor ORDER BY donor_id")
    donors = cur.fetchall()
    if not donors:
        return

    for _ in range(needed):
        donor = random.choice(donors)
        city = donor[2]
        district = donor[3]
        state = donor[4]
        hospital = random.choice(_hospital_rows_for_city(city))
        patient_name = random.choice(NAMES)
        if random.random() < 0.2:
            patient_name = f"{patient_name.split()[0]} {random.choice(['Sharma', 'Rao', 'Naik', 'Patil', 'Nair', 'Iyer'])}"
        blood_group = normalize_blood_group(random.choice(BLOOD_GROUPS))
        units_needed = random.randint(1, 6)
        priority = random.choices(["Normal", "High", "Critical"], weights=[35, 35, 30])[0]
        created_at = _random_datetime(90)
        created_date = created_at.date()
        contact = _unique_phone(set())
        cur.execute(
            "SELECT COALESCE(SUM(units_available),0) FROM city_stock WHERE city=%s AND blood_group=%s",
            (city, blood_group),
        )
        available_units = cur.fetchone()[0] or 0
        stock_shortage = available_units < units_needed or priority == "Critical"
        if stock_shortage:
            priority = "Critical"

        cur.execute(
            """
            INSERT INTO blood_request
            (patient_name, blood_group, units_needed, hospital_name, city, district, state, request_date, created_time, status, priority, contact_number)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
            """,
            (patient_name, blood_group, units_needed, hospital[0], city, district, state, created_date, created_at, "Active", priority, contact),
        )
        request_id = cur.lastrowid
        if stock_shortage:
            cur.execute(
                """
                INSERT INTO emergency_alerts
                (request_id, patient_name, blood_group, city, district, state, hospital_name, urgency_level, required_units, request_time, status)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,'OPEN')
                """,
                (request_id, patient_name, blood_group, city, district, state, hospital[0], "CRITICAL", units_needed, created_at),
            )
        elif random.random() < 0.35:
            cur.execute(
                """
                INSERT INTO emergency_alerts
                (request_id, patient_name, blood_group, city, district, state, hospital_name, urgency_level, required_units, request_time, status)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,'OPEN')
                """,
                (request_id, patient_name, blood_group, city, district, state, hospital[0], priority.upper(), units_needed, created_at),
            )


def seed_donation_history(cur, target_count=30):
    cur.execute("SELECT COUNT(*) FROM donation_history")
    existing_count = cur.fetchone()[0]
    needed = max(0, target_count - existing_count)
    if needed == 0:
        return

    cur.execute("SELECT donor_id, city FROM donor ORDER BY donor_id")
    donors = cur.fetchall()
    if not donors:
        return

    for _ in range(needed):
        donor_id, city = random.choice(donors)
        donation_date = date.today() - timedelta(days=random.randint(5, 820))
        hospital = random.choice(_hospital_rows_for_city(city))
        cur.execute(
            "SELECT COUNT(*) FROM donation_history WHERE donor_id=%s AND donation_date=%s",
            (donor_id, donation_date),
        )
        if cur.fetchone()[0] > 0:
            continue
        cur.execute(
            """
            INSERT INTO donation_history (donor_id, donation_date, units_donated, hospital_name)
            VALUES (%s,%s,%s,%s)
            """,
            (donor_id, donation_date, random.randint(1, 2), hospital[0]),
        )


def seed(min_per_city=MIN_PER_CITY, print_logs=True):
    added_log = {}
    try:
        with get_connection() as conn:
            cur = conn.cursor()
            ensure_hospitals(cur)
            # ensure required cities exist in city_stock
            for city, district, state in REQUIRED_CITIES:
                ensure_city_stock(cur, city, district, state)

            # gather cities from city_stock
            cur.execute("SELECT DISTINCT city, district, state FROM city_stock")
            cities = cur.fetchall()

            # existing contacts/emails
            cur.execute("SELECT contact_number, email FROM donor WHERE contact_number IS NOT NULL")
            existing = set(r[0] for r in cur.fetchall() if r[0])
            # ensure emails tracked too
            cur.execute("SELECT email FROM donor WHERE email IS NOT NULL")
            existing_emails = set(r[0] for r in cur.fetchall() if r[0])

            for city, district, state in cities:
                cur.execute("SELECT COUNT(*) FROM donor WHERE city=%s", (city,))
                count = cur.fetchone()[0]
                need = max(0, min_per_city - count)
                added = 0
                for _ in range(need):
                    # pick a realistic unused name
                    name = random.choice(NAMES)
                    # try to avoid exact name duplicates per city by appending number occasionally
                    if random.random() < 0.08:
                        name = f"{name} {random.randint(2,99)}"
                    age = _rand_age()
                    gender = _rand_gender()
                    bg = normalize_blood_group(random.choice(BLOOD_GROUPS))
                    phone = _unique_phone(existing)
                    email = _make_email(name, phone)
                    # ensure email unique
                    if email in existing_emails:
                        email = f"{email.split('@')[0]}{random.randint(10,99)}@example.com"
                    existing_emails.add(email)

                    avail = random.choices(["Available", "Recently Donated", "Inactive"], weights=[60,25,15])[0]
                    last_donation = None
                    today = date.today()
                    if avail == "Recently Donated":
                        last_donation = today - timedelta(days=random.randint(7, 90))
                    elif avail == "Available":
                        if random.random() < 0.6:
                            last_donation = today - timedelta(days=random.randint(100, 900))

                    donor = Donor(
                        full_name=name,
                        age=age,
                        gender=gender,
                        blood_group=bg,
                        city=city,
                        district=district,
                        state=state,
                        availability_status=avail,
                        contact_number=phone,
                        email=email,
                        last_donation_date=last_donation,
                    )

                    ok = DonorService.add_donor(donor)
                    if ok:
                        added += 1
                        # insert donation history if present
                        if donor.last_donation_date:
                            try:
                                cur.execute("SELECT donor_id FROM donor WHERE contact_number=%s", (phone,))
                                row = cur.fetchone()
                                if row:
                                    donor_id = row[0]
                                    cur.execute(
                                        "SELECT COUNT(*) FROM donation_history WHERE donor_id=%s AND donation_date=%s",
                                        (donor_id, donor.last_donation_date),
                                    )
                                    if cur.fetchone()[0] == 0:
                                        cur.execute(
                                            "INSERT INTO donation_history (donor_id, donation_date, units_donated) VALUES (%s,%s,%s)",
                                            (donor_id, donor.last_donation_date, 1),
                                        )
                                        conn.commit()
                            except Error:
                                logger.exception("Could not insert donation history for %s", phone)

                if print_logs:
                    if added > 0:
                        logger.info("Added %s donors for %s", added, city)
                    else:
                        logger.info("No additions needed for %s", city)
                added_log[city] = added

            seed_requests(cur, target_count=20)
            seed_donation_history(cur, target_count=30)

            # final commit
            conn.commit()
    except Error:
        logger.exception("Seeding failed")
        return {}

    return added_log


if __name__ == "__main__":
    seed()
