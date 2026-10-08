#!/usr/bin/env python3
"""Prepare the database: create it, or bring it to the latest revision (Q6.6)."""

import sys
from pathlib import Path

# Put the repository root first, so that the script imports backend.app from
# its own checkout, under the same module names as the application.
repo_root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(repo_root))

from backend.app.data_access.database import DATABASE_URL, loggable_url  # noqa: E402
from backend.app.data_access.schema import SchemaError, prepare_database  # noqa: E402
from backend.app.logger import CustomLogger  # noqa: E402

logger = CustomLogger("DBInit")


def init_database() -> None:
    """Bring the configured database to the latest revision, or exit with 1."""
    # Without password and query: INFO lines are printed now (TD-3).
    logger.info("Preparing database at: %s", loggable_url(DATABASE_URL))
    try:
        outcome = prepare_database(DATABASE_URL)
    except SchemaError as exc:
        # The schema diff is meant for the operator: printed as is, logged as one line.
        print(exc, file=sys.stderr)
        logger.error("Database not prepared: %s", exc)
        sys.exit(1)
    except Exception as exc:
        # A migration's message says what to set (for example the time zone);
        # the log line is cut, so the operator gets it in full here.
        print(f"Database preparation failed: {exc}", file=sys.stderr)
        logger.error("Database preparation failed: %s", exc)
        sys.exit(1)
    logger.info("Database ready: %s", outcome)


if __name__ == "__main__":
    init_database()
