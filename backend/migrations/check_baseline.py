#!/usr/bin/env python3
"""Check an existing SQLite database against the baseline schema before stamping it.

    python backend/migrations/check_baseline.py <database.db>

A database made before Alembic has no alembic_version table. It may be
stamped at the baseline revision (alembic stamp head) only if its schema is
exactly the baseline: sqlite_master as Base.metadata.create_all leaves a
fresh database, which is also what revision 0001 creates. A database made
from an older model (without the CHECK constraints, or with an id index)
must not be stamped, since later revisions would assume a schema it does
not have.

Exit codes:
    0  the schema equals the baseline; stamping may follow
    1  the schema differs; a unified diff against the baseline is printed
    2  no such file, or the database is already under Alembic

The database is opened read-only. Standard library only.
"""

import difflib
import sqlite3
import sys
from pathlib import Path

# sqlite_master rows (type, name, tbl_name, sql), ordered by type and name.
BASELINE_SCHEMA = [
    (
        "index",
        "ix_toDo_title",
        "toDo",
        'CREATE INDEX "ix_toDo_title" ON "toDo" (title)',
    ),
    ("index", "sqlite_autoindex_toDo_1", "toDo", None),
    (
        "table",
        "toDo",
        "toDo",
        'CREATE TABLE "toDo" (\n'
        "\tid CHAR(32) NOT NULL, \n"
        "\ttitle VARCHAR(255) NOT NULL, \n"
        "\tdescription VARCHAR(255), \n"
        "\tcreated_at TIMESTAMP NOT NULL, \n"
        "\tupdated_at TIMESTAMP, \n"
        "\tdeleted BOOLEAN NOT NULL, \n"
        "\tdone BOOLEAN NOT NULL, \n"
        "\tPRIMARY KEY (id), \n"
        "\tCONSTRAINT title_length_check CHECK (length(title) <= 255), \n"
        "\tCONSTRAINT description_length_check CHECK (length(description) <= 255)\n"
        ")",
    ),
]

VERSION_TABLE = "alembic_version"


def read_schema(path: Path) -> list[tuple[str, str, str, str | None]]:
    """sqlite_master of the database, without Alembic's own version table."""
    connection = sqlite3.connect(f"{path.resolve().as_uri()}?mode=ro", uri=True)
    try:
        rows: list[tuple[str, str, str, str | None]] = connection.execute(
            "SELECT type, name, tbl_name, sql FROM sqlite_master "
            "WHERE tbl_name != ? ORDER BY type, name",
            (VERSION_TABLE,),
        ).fetchall()
    finally:
        connection.close()
    return rows


def is_versioned(path: Path) -> bool:
    connection = sqlite3.connect(f"{path.resolve().as_uri()}?mode=ro", uri=True)
    try:
        found = connection.execute(
            "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = ?",
            (VERSION_TABLE,),
        ).fetchone()
    finally:
        connection.close()
    return found is not None


def render(schema: list[tuple[str, str, str, str | None]]) -> list[str]:
    lines = []
    for kind, name, table, sql in schema:
        lines.append(f"-- {kind} {name} on {table}")
        lines.extend((sql or "(no SQL: created by SQLite)").splitlines())
    return lines


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
        print(f"{path}: schema equals the baseline; alembic stamp head may follow")
        return 0
    diff = difflib.unified_diff(
        render(BASELINE_SCHEMA), render(schema), "baseline", str(path), lineterm=""
    )
    print("\n".join(diff))
    print(f"{path}: schema differs from the baseline; do not stamp", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
