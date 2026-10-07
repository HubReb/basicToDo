"""SQLite database files: where the default one lives, and who may read it (SEC-014).

The legacy code put the database at backend/todo.db under the working
directory, with SQLite's default mode (0644 under the usual umask), so every
local user could read the todos. Now a missing file is created 0600 before
SQLite opens it, through the do_connect hook of each engine that may create
it: the application's and the one that prepares the database at startup.
At an engine's first connection, an existing file of this process's owner
is restricted to 0600 if it is the default database or still empty; any
other existing file keeps the mode its operator chose, and group or other
access is reported. Failures are reported, never raised, so they cannot
break a connection. SQLite gives its -journal, -wal and -shm files the mode
of the database file.
"""

import os
from pathlib import Path
from typing import Any

from sqlalchemy import event
from sqlalchemy.engine import Engine, make_url

from backend.app.logger import CustomLogger

# Next to the backend package, wherever the process was started from (it
# used to follow the working directory).
DEFAULT_DATABASE_PATH = Path(__file__).resolve().parents[2] / "todo.db"

_logger = CustomLogger("DatabaseFile")


def sqlite_file(url: str) -> Path | None:
    """The file of a file-backed SQLite URL; None for anything else."""
    parsed = make_url(url)
    if (
        parsed.get_backend_name() != "sqlite"
        or parsed.database in (None, "", ":memory:")
        or parsed.query.get("uri")
    ):
        return None
    return Path(parsed.database)


def create_owner_only(path: Path) -> None:
    """Create a missing database file with mode 0600, before SQLite would create it 0644."""
    try:
        os.close(os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600))
    except FileExistsError:
        pass
    except OSError as exc:
        # SQLite reports the problem itself when it opens the file.
        _logger.warning("Could not create database file %s: %s", path, exc)


def restrict_to_owner(path: Path) -> None:
    """0600 for the default database or an empty one of this owner; report others."""
    try:
        info = path.stat()
    except OSError:
        return
    if info.st_uid != os.geteuid() or not info.st_mode & 0o077:
        return
    if path.resolve() != DEFAULT_DATABASE_PATH and info.st_size > 0:
        _logger.warning("Database file %s is accessible to group or others", path)
        return
    try:
        path.chmod(0o600)
    except OSError as exc:
        _logger.warning(
            "Could not restrict database file %s to its owner: %s", path, exc
        )


def protect(engine: Engine, url: str) -> None:
    """New files 0600 on every connect; the existing file checked at the first one."""
    path = sqlite_file(url)
    if path is None:
        return

    @event.listens_for(engine, "do_connect")
    def _create_owner_only(
        dialect: Any, connection_record: Any, cargs: Any, cparams: Any
    ) -> None:
        create_owner_only(path)

    @event.listens_for(engine, "connect", once=True)
    def _restrict_to_owner(dbapi_connection: Any, connection_record: Any) -> None:
        restrict_to_owner(path)
