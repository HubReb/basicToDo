#!/usr/bin/env python3
"""Check an existing SQLite database against the baseline schema.

    python backend/migrations/check_baseline.py <database.db>

A database made before Alembic has no alembic_version table. The
application stamps it at the baseline revision 0001 and upgrades it at
startup only if its schema is exactly the baseline: sqlite_master as
Base.metadata.create_all leaves a fresh database, which is also what
revision 0001 creates (backend/app/data_access/schema.py). This script runs
the same check by hand, for example before a manual
"alembic stamp 0001" followed by "alembic upgrade head". A database made
from an older model (without the CHECK constraints, or with an id index)
must not be stamped, since later revisions assume a schema it does not have.

Exit codes:
    0  the schema equals the baseline
    1  the schema differs; a unified diff against the baseline is printed
    2  no such file, or the database is already under Alembic

The database is opened read-only.
"""

import sqlite3
import sys
from pathlib import Path

# The repository root, so that backend.app comes from this checkout.
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from backend.app.data_access.schema import (  # noqa: E402
    BASELINE_SCHEMA,
    VERSION_TABLE,
    SchemaRow,
    render,
    schema_diff,
)
from backend.app.data_access.schema import read_schema as _read_schema  # noqa: E402

__all__ = [
    "BASELINE_SCHEMA",
    "VERSION_TABLE",
    "is_versioned",
    "main",
    "read_schema",
    "render",
]


def _connect(path: Path) -> sqlite3.Connection:
    return sqlite3.connect(f"{path.resolve().as_uri()}?mode=ro", uri=True)


def read_schema(path: Path) -> list[SchemaRow]:
    """sqlite_master of the database, without Alembic's own version table."""
    connection = _connect(path)
    try:
        return _read_schema(connection)
    finally:
        connection.close()


def is_versioned(path: Path) -> bool:
    connection = _connect(path)
    try:
        found = connection.execute(
            "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = ?",
            (VERSION_TABLE,),
        ).fetchone()
    finally:
        connection.close()
    return found is not None


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print(__doc__, file=sys.stderr)
        return 2
    path = Path(argv[1])
    if not path.is_file():
        print(f"{path}: no such file", file=sys.stderr)
        return 2
    if is_versioned(path):
        print(
            f"{path}: already under Alembic; check it with alembic current",
            file=sys.stderr,
        )
        return 2

    schema = read_schema(path)
    if schema == BASELINE_SCHEMA:
        print(f"{path}: schema equals the baseline; alembic stamp 0001 may follow")
        return 0
    print(schema_diff(schema, str(path)))
    print(f"{path}: schema differs from the baseline; do not stamp", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
