"""Database connection helper for BloodBridge."""
import logging
import re
from contextlib import contextmanager

import mysql.connector
from mysql.connector import Error

from config import db_config


logger = logging.getLogger(__name__)
_DB_NAME_PATTERN = re.compile(r"^[A-Za-z0-9_]+$")


@contextmanager
def get_connection():
    """Context manager that yields a DB connection and ensures close on exit."""
    if not _DB_NAME_PATTERN.fullmatch(db_config.DB_NAME):
        raise ValueError("DB_NAME must contain only letters, numbers, and underscores")

    conn = None
    cur = None
    try:
        conn = mysql.connector.connect(
            host=db_config.DB_HOST,
            user=db_config.DB_USER,
            password=db_config.DB_PASSWORD,
            port=db_config.DB_PORT,
        )
        cur = conn.cursor()
        cur.execute(f"CREATE DATABASE IF NOT EXISTS `{db_config.DB_NAME}`")
        cur.execute(f"USE `{db_config.DB_NAME}`")
        yield conn
    except Error:
        logger.exception("Database connection failed")
        raise
    finally:
        if cur:
            cur.close()
        if conn and conn.is_connected():
            conn.close()
