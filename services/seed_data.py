"""Backward-compatible wrapper for the standalone seeding command.

This module now delegates to :mod:`database.seed_database` so there is only one
non-destructive demo seeding implementation to maintain.
"""

import logging

from database.seed_database import seed


logger = logging.getLogger(__name__)


def seed_dummy_donors(min_per_city=2, print_logs=True):
    """Seed demo donors by delegating to the standalone database command."""

    return seed(min_per_city=min_per_city, print_logs=print_logs)


if __name__ == "__main__":
    logger.info("Running standalone donor seed wrapper")
    seed_dummy_donors()
