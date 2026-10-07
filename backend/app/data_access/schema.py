"""The database schema at startup: Alembic at runtime, with a baseline check and a backup (Q6.6).

prepare_database() brings a SQLite database to the latest revision, on one
connection and in one transaction:

- no tables yet (a new or empty file): upgrade from the start, no backup;
- tables but no Alembic version (made before Alembic): only if the schema
  equals BASELINE_SCHEMA, back up, stamp the baseline revision and
  upgrade; any other schema stops with a diff, and nothing is written;
- an older revision: back up and upgrade;
- the latest revision: nothing to do.

The transaction starts with BEGIN IMMEDIATE, so no other process writes
meanwhile, and the DDL belongs to it: pysqlite would otherwise commit DDL
on its own, and a failing migration would leave a half-versioned file. The
backup, <name>.pre-<revision>.bak, is made with SQLite's backup API through
a second, read-only connection (SQLite refuses a backup from the connection
holding the write lock); it includes changes still in a WAL file. It is
checked (integrity_check, then every table row by row against the source)
before anything is written. Any error rolls the transaction back and
removes the backup.
"""

import difflib
import os
import sqlite3
from pathlib import Path
from typing import Any, cast

from alembic import command
from alembic.config import Config
from alembic.script import ScriptDirectory
from sqlalchemy import create_engine, event
from sqlalchemy.engine import Connection, Engine, make_url
from sqlalchemy.pool import NullPool

MIGRATIONS = Path(__file__).resolve().parents[2] / "migrations"
BASELINE_REVISION = "0001"
VERSION_TABLE = "alembic_version"

# sqlite_master rows (type, name, tbl_name, sql) of the baseline, ordered by
# type and name: what Base.metadata.create_all and revision 0001 create.
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

SchemaRow = tuple[str, str, str, str | None]


class SchemaError(RuntimeError):
    """The database cannot be brought to the latest revision safely."""


def alembic_config(connection: Connection | None = None) -> Config:
    """The migrations of this package, independent of the working directory."""
    config = Config()
    config.set_main_option("script_location", str(MIGRATIONS).replace("%", "%%"))
    if connection is not None:
        config.attributes["connection"] = connection
    return config


def head_revision() -> str:
    head = ScriptDirectory.from_config(alembic_config()).get_current_head()
    if head is None:
        raise SchemaError("no migration revisions found")
    return head


def read_schema(dbapi_connection: sqlite3.Connection) -> list[SchemaRow]:
    """sqlite_master without Alembic's version table, ordered by type and name."""
    rows = dbapi_connection.execute(
        "SELECT type, name, tbl_name, sql FROM sqlite_master "
        "WHERE tbl_name != ? ORDER BY type, name",
        (VERSION_TABLE,),
    ).fetchall()
    return [tuple(row) for row in rows]


def render(schema: list[SchemaRow]) -> list[str]:
    lines = []
    for kind, name, table, sql in schema:
        lines.append(f"-- {kind} {name} on {table}")
        lines.extend((sql or "(no SQL: created by SQLite)").splitlines())
    return lines


def schema_diff(schema: list[SchemaRow], label: str) -> str:
    return "\n".join(
        difflib.unified_diff(
            render(BASELINE_SCHEMA), render(schema), "baseline", label, lineterm=""
        )
    )


def _tables(dbapi_connection: sqlite3.Connection) -> list[str]:
    rows = dbapi_connection.execute(
        "SELECT name FROM sqlite_master WHERE type = 'table' "
        "AND name NOT LIKE 'sqlite_%' ORDER BY name"
    ).fetchall()
    return [row[0] for row in rows]


def _current_revision(dbapi_connection: sqlite3.Connection) -> str | None:
    if VERSION_TABLE not in _tables(dbapi_connection):
        return None
    row = dbapi_connection.execute(
        f"SELECT version_num FROM {VERSION_TABLE}"
    ).fetchone()
    return None if row is None else str(row[0])


def _rows(dbapi_connection: sqlite3.Connection, table: str) -> list[Any]:
    columns = dbapi_connection.execute(f'PRAGMA table_info("{table}")').fetchall()
    key = [f'"{c[1]}"' for c in sorted(columns, key=lambda c: c[5]) if c[5] > 0]
    order = ", ".join(key) or "rowid"
    return dbapi_connection.execute(
        f'SELECT * FROM "{table}" ORDER BY {order}'
    ).fetchall()


def _sqlite_path(url: str) -> Path:
    parsed = make_url(url)
    if parsed.get_backend_name() != "sqlite" or parsed.database in (
        None,
        "",
        ":memory:",
    ):
        raise SchemaError("only SQLite database files are prepared")
    return Path(parsed.database)


def _backup(path: Path, revision: str, source: sqlite3.Connection) -> Path:
    """A checked copy of the database, never overwriting an earlier one."""
    target = path.with_name(f"{path.name}.pre-{revision}.bak")
    try:
        os.close(os.open(target, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600))
    except FileExistsError as exc:
        raise SchemaError(f"{target} exists; move it away before migrating") from exc
    try:
        reader = sqlite3.connect(f"{path.resolve().as_uri()}?mode=ro", uri=True)
        copy = sqlite3.connect(target)
        try:
            reader.backup(copy)
            check = copy.execute("PRAGMA integrity_check").fetchall()
            if check != [("ok",)]:
                raise SchemaError(f"the backup {target} fails integrity_check: {check}")
            if _tables(copy) != _tables(source):
                raise SchemaError(f"the backup {target} lacks tables of the source")
            for table in _tables(source):
                if _rows(copy, table) != _rows(source, table):
                    raise SchemaError(
                        f"the backup {target} differs from the source in {table}"
                    )
        finally:
            reader.close()
            copy.close()
    except BaseException:
        target.unlink(missing_ok=True)
        raise
    return target


def _locking_engine(url: str) -> Engine:
    """One connection, one transaction that starts with BEGIN IMMEDIATE and includes DDL."""
    engine = create_engine(url, poolclass=NullPool)

    @event.listens_for(engine, "connect")
    def _no_implicit_transactions(dbapi_connection: Any, record: Any) -> None:
        dbapi_connection.isolation_level = None

    @event.listens_for(engine, "begin")
    def _begin_immediate(connection: Connection) -> None:
        connection.exec_driver_sql("BEGIN IMMEDIATE")

    return engine


def prepare_database(url: str) -> str:
    """Bring the database to the latest revision; returns what was done."""
    path = _sqlite_path(url)
    head = head_revision()
    engine = _locking_engine(url)
    backup: Path | None = None
    try:
        with engine.begin() as connection:
            # The DBAPI protocol type does not overlap sqlite3.Connection for mypy.
            dbapi = cast(sqlite3.Connection, connection.connection.dbapi_connection)
            current = _current_revision(dbapi)
            if not _tables(dbapi):
                command.upgrade(alembic_config(connection), "head")
                outcome = f"created at revision {head}"
            elif current is None:
                schema = read_schema(dbapi)
                if schema != BASELINE_SCHEMA:
                    raise SchemaError(
                        f"{path} was made before Alembic, but its schema is not the baseline; "
                        "nothing was changed.\n" + schema_diff(schema, str(path))
                    )
                backup = _backup(path, head, dbapi)
                command.stamp(alembic_config(connection), BASELINE_REVISION)
                command.upgrade(alembic_config(connection), "head")
                outcome = f"stamped {BASELINE_REVISION} and upgraded to {head}"
            elif current == head:
                outcome = f"already at revision {head}"
            else:
                backup = _backup(path, head, dbapi)
                command.upgrade(alembic_config(connection), "head")
                outcome = f"upgraded from {current} to {head}"
    except BaseException:
        if backup is not None:
            backup.unlink(missing_ok=True)
        raise
    finally:
        engine.dispose()
    return outcome if backup is None else f"{outcome}; backup {backup.name}"


def current_revision(url: str) -> str | None:
    """The database's Alembic revision, or None (also for a missing file)."""
    path = _sqlite_path(url)
    if not path.exists():
        return None
    connection = sqlite3.connect(f"{path.resolve().as_uri()}?mode=ro", uri=True)
    try:
        return _current_revision(connection)
    finally:
        connection.close()


def assert_at_head(url: str) -> None:
    """Refuse to serve a database that is not at the latest revision."""
    current, head = current_revision(url), head_revision()
    if current != head:
        raise SchemaError(
            f"the database is at revision {current or '(none)'}, not {head}; "
            "prepare it first: python backend/scripts/init_db.py"
        )
