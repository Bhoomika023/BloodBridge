# BloodBridge - Smart Emergency Blood Coordination Platform

BloodBridge is a Python, CustomTkinter, and MySQL DBMS project for coordinating emergency blood requests. It tracks city-wise blood stock, donor availability, emergency requests, priority alerts, donation history, and analytics through a single desktop dashboard.

> **Note:** This project uses **fictional (dummy) data** for demonstration and academic purposes only. No real patient, donor, hospital, or medical information is included in this repository.

---

## Features

- City-wise blood stock dashboard with Safe, Low, and Critical indicators
- Emergency request creation with priority-based workflow
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
- Pillow

---

## Installation

Clone the repository.

```bash
git clone https://github.com/Bhoomika023/BloodBridge.git

cd BloodBridge
```

Create and activate a virtual environment.

```bash
python -m venv .venv
```

Windows

```bash
.venv\Scripts\activate
```

Linux/macOS

```bash
source .venv/bin/activate
```

Install the dependencies.

```bash
pip install -r requirements.txt
```

---

## Environment Setup

1. Copy `.env.example` to `.env`.
2. Update the file with your local MySQL credentials.

Example:

```env
DB_HOST=localhost
DB_USER=root
DB_PASSWORD=your-local-password
DB_NAME=bloodbridge_db
DB_PORT=3306
```

Never commit `.env` or real database credentials.

---

## Database Setup

BloodBridge automatically:

- Creates the database (if it does not exist)
- Creates all required tables
- Safely upgrades the schema without deleting existing data

Run the application:

```bash
python main.py
```

Optional manual schema setup:

```sql
source database/schema.sql;
```

Optional demo data seeding:

```bash
python -m database.seed_database
```

The demo seeder is intentionally **non-destructive**. It only inserts missing demo data and never overwrites existing records or blood stock.

---

## Demo Data

This project includes realistic dummy data representing:

- Blood donors
- Hospitals
- Emergency requests
- Blood inventory
- Donation history
- Emergency alerts

All names, phone numbers, hospitals, and records are fictional and included solely for demonstration purposes.

---

## Demo Workflow

1. Launch the application.
2. Open the Dashboard.
3. Create an emergency blood request.
4. Review the emergency alert banner and matching donors.
5. Search donors by blood group, availability, city, or district.
6. Arrange blood and resolve the request.
7. Review Donation History.
8. Explore the Analytics dashboard.

---

## Database Schema

Core tables used in the project:

- `donor` – donor information, availability, and contact details
- `blood_request` – emergency requests with patient, hospital, location, priority, and status
- `emergency_alerts` – emergency coordination records linked to requests
- `city_stock` – city-wise blood inventory
- `hospitals` – hospital information
- `donation_history` – completed donation records

The schema supports foreign keys, indexes, and safe runtime upgrades.

---

## Stock Handling Policy

Creating an emergency request checks the available blood stock and raises a critical alert when inventory is insufficient.

Stock is **not deducted** when a request is created because a request does not necessarily result in blood being issued.

Inventory should only be reduced after blood has actually been arranged or donated, preventing incorrect stock reduction for cancelled or unresolved requests.

---

## Project Structure

```text
BloodBridge/
│
├── assets/
├── config/
├── database/
├── gui/
├── models/
├── services/
├── main.py
├── requirements.txt
├── README.md
├── LICENSE
├── .gitignore
└── .env.example
```

---

## Architecture

- `gui/` contains the CustomTkinter user interface.
- `services/` contains the business logic for donors, requests, alerts, stock management, reporting, validation, and blood compatibility.
- `database/` contains the schema, upgrade scripts, and demo data seeding utilities.
- `config/` manages environment-based database configuration.
- `main.py` is the application entry point.

---

## Future Improvements

- Add automated unit tests
- Export reports to PDF and Excel
- Role-based user authentication
- Email/SMS notification support
- GIS-based nearest donor identification
- Cloud deployment
- Mobile companion application

---

## Academic Notes

BloodBridge demonstrates practical implementation of:

- CRUD Operations
- SQL Queries
- Joins
- Aggregate Functions
- Foreign Keys
- Indexing
- Database Schema Design
- Transactions
- Data Validation
- Dashboard Analytics
- Emergency Workflow Management

---

---

## License

This project is licensed under the MIT License.

See the `LICENSE` file for details.
