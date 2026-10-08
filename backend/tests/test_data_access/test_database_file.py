"""SEC-014: where the default database lives, and that only its owner can read it."""

import logging
import os
import sqlite3
import stat
from pathlib import Path

import pytest
from sqlalchemy import create_engine, event, text
from sqlalchemy.pool import NullPool

from backend.app.data_access import database_file
from backend.app.data_access.database import get_safe_database_url
from backend.app.data_access.database_file import (
    DEFAULT_DATABASE_PATH,
    protect,
    sqlite_file,
)
from backend.app.data_access.schema import prepare_database
from backend.app.logger import ROOT

REPO_ROOT = Path(__file__).resolve().parents[3]


def mode(path: Path) -> int:
    return stat.S_IMODE(path.stat().st_mode)


@pytest.fixture(autouse=True)
def usual_umask():
    previous = os.umask(0o022)
    yield
    os.umask(previous)


@pytest.fixture
def warnings():
    captured: list[str] = []

    class Capture(logging.Handler):
        def emit(self, record: logging.LogRecord) -> None:
            if record.levelno == logging.WARNING:
                captured.append(record.getMessage())

    handler = Capture()
    logging.getLogger(ROOT).addHandler(handler)
    yield captured
    logging.getLogger(ROOT).removeHandler(handler)


def connect(path: Path, times: int = 1) -> None:
    """Connect like the application's engine, through protect()."""
    url = f"sqlite:///{path}"
    engine = create_engine(url, poolclass=NullPool)
    protect(engine, url)
    try:
        for _ in range(times):
            with engine.connect() as connection:
                connection.execute(text("CREATE TABLE IF NOT EXISTS t (x)"))
                connection.commit()
    finally:
        engine.dispose()


def legacy_file(path: Path, content: bool = True) -> Path:
    """A database file as SQLite creates it without protect(): 0644 under umask 022."""
    connection = sqlite3.connect(path)
    if content:
        connection.execute("CREATE TABLE t (x)")
        connection.commit()
    connection.close()
    return path


class TestDefaultPath:
    def test_the_default_database_is_next_to_the_package(self, monkeypatch, tmp_path):
        monkeypatch.delenv("DATABASE_URL", raising=False)
        monkeypatch.chdir(tmp_path)

        assert get_safe_database_url() == f"sqlite:///{DEFAULT_DATABASE_PATH}"
        assert DEFAULT_DATABASE_PATH == REPO_ROOT / "backend" / "todo.db"

    @pytest.mark.parametrize(
        "url",
        [
            "sqlite://",
            "sqlite:///:memory:",
            "postgresql://db/todo",
            "sqlite:///file:x.db?uri=true",
        ],
    )
    def test_only_sqlite_files_are_handled(self, url):
        assert sqlite_file(url) is None


class TestNewFiles:
    def test_without_protection_sqlite_creates_0644(self, tmp_path):
        # Positive control for the tests below.
        assert mode(legacy_file(tmp_path / "plain.db")) == 0o644

    def test_the_application_engine_creates_0600(self, tmp_path):
        connect(tmp_path / "new.db")

        assert mode(tmp_path / "new.db") == 0o600

    def test_a_new_file_is_never_wider_than_0600(self, tmp_path):
        # R2: not created 0644 by SQLite and restricted afterwards, but
        # created 0600 before SQLite opens it.
        path = tmp_path / "new.db"
        url = f"sqlite:///{path}"
        engine = create_engine(url, poolclass=NullPool)
        seen = []

        @event.listens_for(engine, "connect")
        def record(dbapi_connection, connection_record):
            seen.append(mode(path))

        protect(engine, url)
        try:
            with engine.connect():
                pass
        finally:
            engine.dispose()

        assert seen == [0o600]

    def test_the_startup_preparation_creates_0600(self, tmp_path):
        prepare_database(f"sqlite:///{tmp_path / 'new.db'}")

        assert mode(tmp_path / "new.db") == 0o600

    def test_side_files_get_the_database_files_mode(self, tmp_path):
        path = tmp_path / "wal.db"
        connect(path)
        connection = sqlite3.connect(path)
        try:
            connection.execute("PRAGMA journal_mode=WAL")
            connection.execute("INSERT INTO t VALUES (1)")
            connection.commit()
            assert mode(Path(f"{path}-wal")) == 0o600
            assert mode(Path(f"{path}-shm")) == 0o600
        finally:
            connection.close()


class TestExistingFiles:
    def test_another_database_keeps_its_mode_and_is_reported_once(
        self, tmp_path, warnings
    ):
        path = legacy_file(tmp_path / "shared.db")

        connect(path, times=3)

        assert mode(path) == 0o644
        assert warnings == [f"Database file {path} is accessible to group or others"]

    def test_the_default_database_is_restricted(self, tmp_path, monkeypatch):
        path = legacy_file(tmp_path / "todo.db")
        monkeypatch.setattr(database_file, "DEFAULT_DATABASE_PATH", path.resolve())

        connect(path)

        assert mode(path) == 0o600

    def test_an_empty_database_is_restricted(self, tmp_path):
        path = tmp_path / "empty.db"
        path.touch(mode=0o644)

        connect(path)

        assert mode(path) == 0o600

    def test_a_failing_chmod_is_reported_not_raised(
        self, tmp_path, monkeypatch, warnings
    ):
        path = tmp_path / "empty.db"
        path.touch(mode=0o644)

        def refuse(self, mode):
            raise PermissionError("not allowed")

        monkeypatch.setattr(Path, "chmod", refuse)

        connect(path)

        assert warnings == [
            f"Could not restrict database file {path} to its owner: not allowed"
        ]

    def test_an_owner_only_file_is_left_alone(self, tmp_path, warnings):
        path = legacy_file(tmp_path / "private.db")
        path.chmod(0o600)

        connect(path)

        assert (mode(path), warnings) == (0o600, [])
