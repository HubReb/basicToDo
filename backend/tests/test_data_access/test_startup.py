"""The database at startup (Q6.6): prepare_database, its backup, and the app's guard.

prepare_database runs the Alembic revisions on one connection, in one
transaction that starts with BEGIN IMMEDIATE:

- a missing or empty file is created at the latest revision, without backup;
- a database made before Alembic is backed up, stamped 0001 and upgraded,
  but only if its schema is the baseline;
- a database at an older revision is backed up and upgraded;
- one at the latest revision is left alone;
- anything else stops it, and nothing is written.

The backup, <name>.pre-<revision>.bak, is made with SQLite's backup API, so
it includes changes still in a WAL file, and is checked with
integrity_check and row by row against the source before anything changes.
"""

import os
import shutil
import sqlite3
import stat
import subprocess
import sys
from pathlib import Path

import pytest
from alembic import command
from alembic.util import CommandError
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.exc import OperationalError

from backend.app.api import api
from backend.app.data_access import schema
from backend.app.data_access.database import Base
from backend.app.data_access.schema import (
    BASELINE_SCHEMA,
    SchemaError,
    alembic_config,
    assert_at_head,
    current_revision,
    head_revision,
    prepare_database,
)

REPO_ROOT = Path(__file__).resolve().parents[3]
INIT_DB = REPO_ROOT / "backend" / "scripts" / "init_db.py"

# Rows as the legacy code stored them in a zone five hours ahead of UTC:
# created_at local, updated_at the database's UTC clock in whole seconds.
LEGACY_ZONE = "Etc/GMT-5"
LEGACY_ROWS = [
    ("5a3e0000000040008000000000000001", "Buy milk", "two litres",
     "2026-10-08 02:04:11.257988", "2026-10-07 21:04:11", 0, 0),
    ("5a3e0000000040008000000000000002", "Pay rent", None,
     "2026-10-08 02:04:11.268834", "2026-10-07 21:04:11", 0, 1),
    ("5a3e0000000040008000000000000003", "Old UI todo", "not implemented yet",
     "2026-10-08 02:04:11.287085", "2026-10-07 21:04:11", 1, 0),
]  # fmt: skip
MIGRATED_ROWS = [
    ("5a3e0000000040008000000000000001", "Buy milk", "two litres",
     "2026-10-07 21:04:11.257988", "2026-10-07 21:04:11", 0, 0),
    ("5a3e0000000040008000000000000002", "Pay rent", None,
     "2026-10-07 21:04:11.268834", "2026-10-07 21:04:11", 0, 1),
    ("5a3e0000000040008000000000000003", "Old UI todo", None,
     "2026-10-07 21:04:11.287085", "2026-10-07 21:04:11", 1, 0),
]  # fmt: skip
INSERT = 'INSERT INTO "toDo" VALUES (?, ?, ?, ?, ?, ?, ?)'


def url(path: Path) -> str:
    return f"sqlite:///{path}"


def backup_of(path: Path) -> Path:
    return path.with_name(f"{path.name}.pre-{head_revision()}.bak")


def create_all(path: Path) -> None:
    engine = create_engine(url(path))
    Base.metadata.create_all(bind=engine)
    engine.dispose()


def insert(path: Path, rows: list[tuple]) -> None:
    connection = sqlite3.connect(path)
    try:
        connection.executemany(INSERT, rows)
        connection.commit()
    finally:
        connection.close()


def query(path: Path, sql: str) -> list[tuple]:
    connection = sqlite3.connect(path)
    try:
        return connection.execute(sql).fetchall()
    finally:
        connection.close()


def todos(path: Path) -> list[tuple]:
    return query(path, 'SELECT * FROM "toDo" ORDER BY id')


def tables(path: Path) -> list[str]:
    return [
        row[0]
        for row in query(
            path, "SELECT name FROM sqlite_master WHERE type = 'table' ORDER BY name"
        )
    ]


def application_schema(path: Path) -> list[tuple]:
    return query(
        path,
        "SELECT type, name, tbl_name, sql FROM sqlite_master "
        "WHERE tbl_name != 'alembic_version' ORDER BY type, name",
    )


def upgrade(path: Path, revision: str) -> None:
    engine = create_engine(url(path))
    try:
        with engine.begin() as connection:
            command.upgrade(alembic_config(connection), revision)
    finally:
        engine.dispose()


@pytest.fixture(autouse=True)
def legacy_zone(monkeypatch):
    monkeypatch.setenv("BASICTODO_LEGACY_TZ", LEGACY_ZONE)


@pytest.fixture
def legacy_db(tmp_path) -> Path:
    """A database made before Alembic, with rows the legacy code wrote."""
    path = tmp_path / "todo.db"
    create_all(path)
    insert(path, LEGACY_ROWS)
    return path


class TestDecisions:
    def test_a_missing_file_is_created_at_the_latest_revision(self, tmp_path):
        path = tmp_path / "new.db"

        outcome = prepare_database(url(path))

        assert outcome == f"created at revision {head_revision()}"
        assert application_schema(path) == BASELINE_SCHEMA
        assert current_revision(url(path)) == head_revision()
        assert list(tmp_path.glob("*.bak")) == []

    def test_an_empty_file_is_created_at_the_latest_revision(self, tmp_path):
        path = tmp_path / "empty.db"
        path.touch()

        assert prepare_database(url(path)) == f"created at revision {head_revision()}"
        assert application_schema(path) == BASELINE_SCHEMA
        assert list(tmp_path.glob("*.bak")) == []

    def test_a_database_made_before_alembic_is_backed_up_stamped_and_upgraded(
        self, legacy_db
    ):
        outcome = prepare_database(url(legacy_db))

        assert outcome == (
            f"stamped 0001 and upgraded to {head_revision()}; "
            f"backup {backup_of(legacy_db).name}"
        )
        assert todos(legacy_db) == MIGRATED_ROWS
        assert application_schema(legacy_db) == BASELINE_SCHEMA
        assert current_revision(url(legacy_db)) == head_revision()

    def test_a_database_at_0001_is_backed_up_and_upgraded(self, tmp_path):
        path = tmp_path / "at-0001.db"
        upgrade(path, "0001")
        insert(path, LEGACY_ROWS)

        outcome = prepare_database(url(path))

        assert outcome == (
            f"upgraded from 0001 to {head_revision()}; backup {backup_of(path).name}"
        )
        assert todos(path) == MIGRATED_ROWS
        assert todos(backup_of(path)) == LEGACY_ROWS

    def test_a_database_at_the_latest_revision_is_left_alone(self, legacy_db):
        prepare_database(url(legacy_db))
        backup_of(legacy_db).unlink()
        content = legacy_db.read_bytes()

        outcome = prepare_database(url(legacy_db))

        assert outcome == f"already at revision {head_revision()}"
        assert legacy_db.read_bytes() == content
        assert not backup_of(legacy_db).exists()

    def test_a_foreign_schema_is_refused_with_a_diff_and_left_unchanged(
        self, legacy_db
    ):
        connection = sqlite3.connect(legacy_db)
        try:
            connection.execute("CREATE TABLE notes (id INTEGER PRIMARY KEY)")
            connection.commit()
        finally:
            connection.close()
        content = legacy_db.read_bytes()

        with pytest.raises(
            SchemaError, match="its schema is not the baseline"
        ) as error:
            prepare_database(url(legacy_db))

        assert "+-- table notes on notes" in str(error.value)
        assert legacy_db.read_bytes() == content
        assert not backup_of(legacy_db).exists()

    def test_an_unknown_revision_stops_it_and_removes_the_backup(self, legacy_db):
        prepare_database(url(legacy_db))
        backup_of(legacy_db).unlink()
        connection = sqlite3.connect(legacy_db)
        try:
            connection.execute("UPDATE alembic_version SET version_num = 'ffff'")
            connection.commit()
        finally:
            connection.close()
        content = legacy_db.read_bytes()

        with pytest.raises(CommandError, match="ffff"):
            prepare_database(url(legacy_db))

        assert legacy_db.read_bytes() == content
        assert not backup_of(legacy_db).exists()

    @pytest.mark.parametrize(
        "database_url", ["sqlite://", "sqlite:///:memory:", "postgresql://db/todo"]
    )
    def test_only_sqlite_files_are_prepared(self, database_url):
        with pytest.raises(SchemaError, match="only SQLite database files"):
            prepare_database(database_url)


class TestOneTransaction:
    def test_a_failing_migration_leaves_rows_and_schema_unchanged(
        self, legacy_db, monkeypatch
    ):
        # The rows were written five hours ahead of UTC; read in UTC, 0002's
        # zone check fails after it has rewritten every created_at, and after
        # the database was stamped 0001.
        monkeypatch.setenv("BASICTODO_LEGACY_TZ", "UTC")
        schema_before = application_schema(legacy_db)

        with pytest.raises(RuntimeError, match="3 of 3 todos"):
            prepare_database(url(legacy_db))

        assert todos(legacy_db) == LEGACY_ROWS
        assert application_schema(legacy_db) == schema_before
        assert tables(legacy_db) == ["toDo"]
        assert not backup_of(legacy_db).exists()

    def test_the_write_lock_is_taken_before_the_backup(self, legacy_db, monkeypatch):
        # While another connection holds the write lock, prepare_database
        # waits (here 0.1 s instead of pysqlite's 5 s) and gives up before a
        # backup is made or anything is written.
        real_create_engine = schema.create_engine
        monkeypatch.setattr(
            schema,
            "create_engine",
            lambda *args, **kwargs: real_create_engine(
                *args, connect_args={"timeout": 0.1}, **kwargs
            ),
        )
        backups = []
        monkeypatch.setattr(
            schema, "_backup", lambda *args: backups.append(args) or args[0]
        )
        holder = sqlite3.connect(legacy_db, isolation_level=None)
        try:
            holder.execute("BEGIN IMMEDIATE")
            with pytest.raises(OperationalError, match="database is locked"):
                prepare_database(url(legacy_db))
        finally:
            holder.execute("ROLLBACK")
            holder.close()

        assert backups == []
        assert todos(legacy_db) == LEGACY_ROWS
        assert tables(legacy_db) == ["toDo"]
        assert not backup_of(legacy_db).exists()


class TestBackup:
    def test_it_holds_the_rows_before_the_migration_and_is_owner_only(self, legacy_db):
        prepare_database(url(legacy_db))

        backup = backup_of(legacy_db)
        assert stat.S_IMODE(backup.stat().st_mode) == 0o600
        assert query(backup, "PRAGMA integrity_check") == [("ok",)]
        assert todos(backup) == LEGACY_ROWS
        assert application_schema(backup) == BASELINE_SCHEMA
        # Taken before the stamp: the backup is the database as it was.
        assert tables(backup) == ["toDo"]

    def test_an_existing_backup_is_never_overwritten(self, legacy_db):
        backup_of(legacy_db).write_bytes(b"an earlier backup")
        content = legacy_db.read_bytes()

        with pytest.raises(SchemaError, match="exists; move it away"):
            prepare_database(url(legacy_db))

        assert backup_of(legacy_db).read_bytes() == b"an earlier backup"
        assert legacy_db.read_bytes() == content

    def test_a_backup_that_differs_from_the_source_is_removed_and_nothing_changes(
        self, legacy_db, monkeypatch
    ):
        rows = schema._rows

        def one_row_missing_in_the_copy(connection, table):
            found = rows(connection, table)
            name = connection.execute("PRAGMA database_list").fetchone()[2]
            return found[:-1] if name.endswith(".bak") else found

        monkeypatch.setattr(schema, "_rows", one_row_missing_in_the_copy)

        with pytest.raises(SchemaError, match="differs from the source in toDo"):
            prepare_database(url(legacy_db))

        assert not backup_of(legacy_db).exists()
        assert todos(legacy_db) == LEGACY_ROWS
        assert tables(legacy_db) == ["toDo"]

    def test_a_wal_database_is_backed_up_and_migrated_with_what_is_only_in_its_wal(
        self, tmp_path
    ):
        path = tmp_path / "wal.db"
        create_all(path)
        insert(path, LEGACY_ROWS[:1])
        writer = sqlite3.connect(path)
        try:
            assert writer.execute("PRAGMA journal_mode=WAL").fetchone() == ("wal",)
            writer.execute("PRAGMA wal_autocheckpoint=0")
            writer.executemany(INSERT, LEGACY_ROWS[1:])
            writer.commit()
            # Committed, but not yet in the main file: only in -wal.
            assert Path(f"{path}-wal").stat().st_size > 0
            main_file_only = tmp_path / "main-file-only.db"
            shutil.copyfile(path, main_file_only)
            assert todos(main_file_only) == LEGACY_ROWS[:1]
            assert todos(path) == LEGACY_ROWS

            prepare_database(url(path))

            assert todos(backup_of(path)) == LEGACY_ROWS
            assert query(backup_of(path), "PRAGMA integrity_check") == [("ok",)]
            assert todos(path) == MIGRATED_ROWS
        finally:
            writer.close()
        assert todos(path) == MIGRATED_ROWS
        assert current_revision(url(path)) == head_revision()


class TestServingGuard:
    def test_current_revision_of_a_missing_file_is_none(self, tmp_path):
        assert current_revision(url(tmp_path / "missing.db")) is None
        assert not (tmp_path / "missing.db").exists()

    @pytest.mark.parametrize("state", ["missing", "before Alembic", "0001"])
    def test_assert_at_head_refuses_anything_but_the_latest_revision(
        self, tmp_path, state
    ):
        path = tmp_path / "todo.db"
        if state == "before Alembic":
            create_all(path)
        elif state == "0001":
            upgrade(path, "0001")

        with pytest.raises(
            SchemaError, match=f"not {head_revision()}; prepare it first"
        ):
            assert_at_head(url(path))

    def test_the_app_does_not_start_on_an_unprepared_database(
        self, legacy_db, monkeypatch
    ):
        monkeypatch.setattr(api, "DATABASE_URL", url(legacy_db))

        with pytest.raises(SchemaError, match="revision \\(none\\)"):
            with TestClient(api.app):
                pass

        assert tables(legacy_db) == ["toDo"]

    def test_the_app_starts_on_a_prepared_database(self, legacy_db, monkeypatch):
        prepare_database(url(legacy_db))
        monkeypatch.setattr(api, "DATABASE_URL", url(legacy_db))

        with TestClient(api.app) as client:
            assert client.get("/").json() == {"status": "ok"}


class TestInitDb:
    def run(self, path: Path, **env: str) -> subprocess.CompletedProcess:
        return subprocess.run(
            [sys.executable, str(INIT_DB)],
            cwd=REPO_ROOT,
            env={**os.environ, "DATABASE_URL": url(path), **env},
            capture_output=True,
            text=True,
            timeout=120,
            check=False,
        )

    def test_it_prepares_the_configured_database(self, legacy_db):
        result = self.run(legacy_db)

        assert result.returncode == 0, result.stderr
        assert "Database ready: stamped 0001 and upgraded to" in result.stderr
        assert todos(legacy_db) == MIGRATED_ROWS

    def test_a_foreign_schema_exits_1_with_the_diff(self, legacy_db):
        connection = sqlite3.connect(legacy_db)
        try:
            connection.execute("CREATE TABLE notes (id INTEGER PRIMARY KEY)")
            connection.commit()
        finally:
            connection.close()

        result = self.run(legacy_db)

        assert result.returncode == 1
        assert "+-- table notes on notes" in result.stderr
        assert tables(legacy_db) == ["notes", "toDo"]

    def test_a_failing_migration_exits_1_with_its_whole_message(self, legacy_db):
        result = self.run(legacy_db, BASICTODO_LEGACY_TZ="UTC")

        assert result.returncode == 1
        assert (
            "Set BASICTODO_LEGACY_TZ to that zone, or BASICTODO_LEGACY_TZ_CHECK=off"
            in (result.stderr)
        )
        assert todos(legacy_db) == LEGACY_ROWS
