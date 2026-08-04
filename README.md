# BloodBridge - Smart Emergency Blood Coordination Platform

BloodBridge is a Python, CustomTkinter, and MySQL DBMS project for coordinating emergency blood requests. It tracks city-wise stock, donor availability, priority requests, emergency alerts, donation history, and analytics from a single desktop dashboard.

## Features

- City-wise blood stock dashboard with low and critical indicators
- Emergency request creation and priority queue
- Donor matching using medically accurate blood compatibility
- Emergency alerts linked to their source request
- Donor registration, search, and availability updates
- Donation history table with search filters
- Matplotlib analytics for donor distribution, request trends, supply/demand, and city ranking
- Automatic schema creation for classroom/demo setup
- Real-time dashboard refresh for requests, donors, alerts, and reports

## Screenshots

Add screenshots before publishing:

- `screenshots/dashboard.png`
- `screenshots/emergency-network.png`
- `screenshots/analytics.png`

Recommended additions:

- `screenshots/requests.png`
- `screenshots/donation-history.png`

## Tech Stack

- Python 3.x
- CustomTkinter
- MySQL
- mysql-connector-python
- python-dotenv
- Matplotlib

## Installation

1. Clone the repository and enter the project directory.

```bash
cd CrimsonLife
```

2. Create and activate a virtual environment.

```bash
python -m venv .venv
.venv\Scripts\activate
```

3. Install dependencies.

```bash
pip install -r requirements.txt
```

## Environment Setup

1. Copy `.env.example` to `.env`.
2. Fill in your local MySQL credentials.

```env
DB_HOST=localhost
DB_USER=root
DB_PASSWORD=your-local-password
DB_NAME=bloodbridge_db
DB_PORT=3306
```

Never commit `.env` or real passwords.

If you are not using a template file, create `.env` with the same keys shown above.

## Database Setup

BloodBridge creates the database and required tables automatically when the app starts.

The runtime schema is upgraded in place. Existing tables are preserved and missing columns are added without dropping data.

Run the app:

```bash
python main.py
```

Optional manual setup:

```sql
source database/schema.sql;
```

Optional demo data seeding:

```bash
python -m database.seed_database
```

Startup seed data is intentionally non-destructive. It only inserts baseline data when the relevant tables are empty and does not overwrite existing blood stock.

The demo seeder generates realistic Karnataka-style sample data for donors, requests, donation history, and hospitals.

## Demo Workflow

1. Start the app and open the Dashboard.
2. Create a critical emergency request with a city, district, hospital, and contact number.
3. Review the emergency banner, matching donors, and low-stock indicators.
4. Move to Emergency Network to search donors by blood group, availability, and location.
5. Resolve a request and confirm that the analytics and history views refresh.
6. Use Donation History filters to search by donor, city, blood group, hospital, or date.

## Database Schema

Core tables used by the dashboard:

- `donor` - donor identity, location, status, and contact details
- `blood_request` - patient requests with hospital, city, district, state, priority, and status
- `emergency_alerts` - emergency coordination records linked to request rows
- `city_stock` - location and blood-group inventory
- `hospitals` - demo hospital and emergency contact data
- `donation_history` - donation records, units, date, and optional hospital context

The schema is compatible with existing data and is upgraded in place.

## Stock Handling Policy

Creating an emergency request checks city stock and raises a critical alert when stock is insufficient. Stock is not deducted at request creation time because a request is not yet a confirmed issue of blood. Stock should be reduced only after blood is actually arranged or issued, preventing false inventory loss for cancelled or unresolved requests.

## Project Structure

```text
CrimsonLife/
  assets/             Static assets
  config/             Environment-based database configuration
  database/           SQL schema, upgrade script, and seeding command
  gui/                CustomTkinter dashboard
  models/             Simple data models
  services/           Database and business-logic services
  main.py             Application entry point
  requirements.txt    Python dependencies
```

## Architecture

- `gui/dashboard.py` owns the desktop UI, live refresh, dialogs, cards, tables, and charts.
- `services/` contains database-backed business logic for requests, donors, alerts, stock, reporting, and validation.
- `database/seed_database.py` produces realistic demo data without dropping or recreating existing records.
- `services/setup_service.py` performs safe runtime upgrades to keep the schema compatible.

## Future Improvements

- Add automated tests for blood compatibility, request resolution, and stock updates
- Add export/report generation for admin use
- Add screenshot capture and a short demo video for submissions
- Split the dashboard into smaller page modules if the UI grows further
- Add user authentication if the project is expanded beyond demo scope
- Add donor distance scoring if geocoding becomes available

## Academic Notes

BloodBridge demonstrates DBMS concepts including CRUD operations, joins, aggregate reports, transactions, foreign keys, indexes, schema setup, and realistic emergency-priority workflows.

## Screenshots Checklist

Before final submission, capture:

- Dashboard overview with a critical alert
- Emergency network with donor matching
- Emergency request page with the queue and matching donor counts
- Donation history with filters
- Analytics dashboard with the expanded charts
