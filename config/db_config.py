"""Database configuration for BloodBridge.

Values are read from a local .env file or environment variables. Keep real
passwords out of source control; use .env.example as the template.
"""
import os
from pathlib import Path

from dotenv import load_dotenv


PROJECT_ROOT = Path(__file__).resolve().parents[1]
load_dotenv(PROJECT_ROOT / ".env")

DB_HOST = os.getenv("DB_HOST", "localhost")
DB_USER = os.getenv("DB_USER", "root")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")
DB_NAME = os.getenv("DB_NAME", "bloodbridge_db")
DB_PORT = int(os.getenv("DB_PORT", "3306"))
