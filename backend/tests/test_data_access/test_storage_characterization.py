"""Characterization of what the data layer stores in the toDo table.

RULE-034 and RULE-035 as changed by Q6.6 (Phase 5): a new ToDo gets one UTC
instant from the builder for both created_at and updated_at, stored as text
without an offset ("YYYY-MM-DD HH:MM:SS.ffffff", which the model defines as
UTC) whatever the server's zone; every change refreshes updated_at. The
legacy pins (created_at in server-local time, updated_at from the database
clock and never refreshed) were replaced, not edited.
RULE-037: the creation path always persists deleted = false.

Everything runs through the real builder and repository on a file-backed
SQLite database, and the stored values are read back raw with sqlite3. The
module imports only Base, ToDoEntryData, ToDoRepository and the builder, so it
ran unchanged against the legacy dual mapping and against the declarative
model that replaced it in Phase 4. Phase 4 changed two behaviours on purpose,
and their tests were replaced rather than edited: the model default for
deleted, and string ids at the repository.
"""

import asyncio
import datetime
import os
import re
import sqlite3
import time
import uuid
from contextlib import contextmanager
from typing import Generator

import pytest
from sqlalchemy import create_engine
from sqlalchemy.exc import StatementError
from sqlalchemy.orm import Session, sessionmaker

from backend.app.business_logic.todo_service import ToDoService
from backend.app.data_access.database import Base
from backend.app.data_access.repository import ToDoRepository
from backend.app.logger import CustomLogger
from backend.app.models.todo import ToDoEntryData
from backend.app.schemas.data_schemes.create_todo_schema import ToDoCreateScheme
from backend.app.schemas.data_schemes.update_todo_schema import TodoUpdateScheme

# sqlite_master of a fresh database, as Base.metadata.create_all leaves it on
# the legacy code (legacy/basictodo at a2d59f1, legacy lock) and on Phase 3.
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

# A zone without DST, five hours ahead of UTC, so that a server-local time
# would be told apart from UTC (CI runners use UTC).
LOCAL_ZONE = "Etc/GMT-5"

STORED_FORMAT = re.compile(r"^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\.\d{6}$")


@pytest.fixture
def local_clock() -> Generator[None, None, None]:
    """Run the test with the process in LOCAL_ZONE, then restore the zone."""
    previous = os.environ.get("TZ")
    os.environ["TZ"] = LOCAL_ZONE
    time.tzset()
    try:
        yield
    finally:
        if previous is None:
            del os.environ["TZ"]
        else:
            os.environ["TZ"] = previous
        time.tzset()


@pytest.fixture
def db_path(tmp_path):
    """Path of a fresh SQLite file with the schema from Base.metadata."""
    path = tmp_path / "storage.db"
    engine = create_engine(f"sqlite:///{path}")
    Base.metadata.create_all(bind=engine)
    engine.dispose()
    return path


@pytest.fixture
def repository(db_path) -> Generator[ToDoRepository, None, None]:
    """The real repository, wired like backend.app.data_access.database.safe_session_scope."""
    engine = create_engine(f"sqlite:///{db_path}")
    session_local = sessionmaker(
        autocommit=False, autoflush=False, bind=engine, expire_on_commit=False
    )

    @contextmanager
    def session_scope() -> Generator[Session, None, None]:
        session = session_local()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    yield ToDoRepository(session_scope, CustomLogger("StorageCharacterization"))
    engine.dispose()


@pytest.fixture
def service(
    repository,
    session_logger,
    session_input_sanitizer,
    session_uuid_validator,
    session_field_validator,
    session_builder,
):
    """The real service on the real repository."""
    return ToDoService(
        repository=repository,
        logger=session_logger,
        input_sanitizer=session_input_sanitizer,
        uuid_validator=session_uuid_validator,
        field_validator=session_field_validator,
        builder=session_builder,
    )


def raw_rows(db_path) -> list[dict]:
    """Every stored row, as SQLite holds it, with the storage class of each value."""
    connection = sqlite3.connect(db_path)
    connection.row_factory = sqlite3.Row
    try:
        rows = connection.execute(
            "SELECT id, title, description, created_at, updated_at, deleted, done, "
            "typeof(created_at) AS created_at_type, typeof(updated_at) AS updated_at_type, "
            'typeof(deleted) AS deleted_type, typeof(done) AS done_type FROM "toDo"'
        ).fetchall()
    finally:
        connection.close()
    return [dict(row) for row in rows]


def set_raw_updated_at(db_path, todo_id: uuid.UUID, value: str) -> None:
    connection = sqlite3.connect(db_path)
    try:
        connection.execute(
            'UPDATE "toDo" SET updated_at = ? WHERE id = ?', (value, todo_id.hex)
        )
        connection.commit()
    finally:
        connection.close()


def build_entry(
    builder, todo_id: uuid.UUID, title: str = "Wash dishes"
) -> ToDoEntryData:
    return asyncio.run(
        builder.build_from_create_schema(
            ToDoCreateScheme(id=todo_id, title=title, description="by hand")
        )
    )


def utc_now() -> datetime.datetime:
    return datetime.datetime.now(datetime.timezone.utc)


def as_utc(stored: str) -> datetime.datetime:
    """A stored timestamp, read as the model defines it: UTC."""
    return datetime.datetime.fromisoformat(stored).replace(tzinfo=datetime.timezone.utc)


class TestSchema:
    def test_create_all_ddl_equals_the_baseline_snapshot(self, db_path):
        connection = sqlite3.connect(db_path)
        try:
            schema = connection.execute(
                "SELECT type, name, tbl_name, sql FROM sqlite_master ORDER BY type, name"
            ).fetchall()
        finally:
            connection.close()

        assert schema == BASELINE_SCHEMA


class TestCreatedAtRule034:
    def test_created_at_is_stored_as_utc_with_microseconds(
        self, local_clock, session_builder, repository, db_path
    ):
        # Q6.6 replaced the legacy pin (naive server-local time).
        before = utc_now()
        repository.create_to_do(build_entry(session_builder, uuid.uuid4()))
        after = utc_now()

        (row,) = raw_rows(db_path)
        assert row["created_at_type"] == "text"
        assert STORED_FORMAT.match(row["created_at"])
        assert before <= as_utc(row["created_at"]) <= after

    def test_new_todo_is_stored_not_done(self, session_builder, repository, db_path):
        repository.create_to_do(build_entry(session_builder, uuid.uuid4()))

        (row,) = raw_rows(db_path)
        assert (row["done"], row["done_type"]) == (0, "integer")


class TestUpdatedAtRule035:
    def test_insert_stores_updated_at_equal_to_created_at(
        self, local_clock, session_builder, repository, db_path
    ):
        # Q6.6 replaced the legacy pin (the database's UTC clock, whole seconds).
        entry = build_entry(session_builder, uuid.uuid4())
        assert entry.updated_at == entry.created_at

        repository.create_to_do(entry)

        (row,) = raw_rows(db_path)
        assert row["updated_at_type"] == "text"
        assert STORED_FORMAT.match(row["updated_at"])
        assert row["updated_at"] == row["created_at"]

    def test_the_created_object_carries_its_stored_timestamps_in_utc(
        self, local_clock, session_builder, repository, db_path
    ):
        entry = build_entry(session_builder, uuid.uuid4())
        repository.create_to_do(entry)

        (row,) = raw_rows(db_path)
        assert entry.created_at == as_utc(row["created_at"])
        assert entry.updated_at == as_utc(row["updated_at"])
        found = repository.get_to_do_entry(entry.id)
        assert found is not None
        assert found.created_at == as_utc(row["created_at"])
        assert found.created_at.tzinfo is datetime.timezone.utc
        assert found.updated_at == as_utc(row["updated_at"])

    def test_edit_done_and_delete_refresh_updated_at(
        self, session_builder, repository, service, db_path
    ):
        # Q6.6 replaced the legacy pin (updated_at never refreshed).
        todo_id = uuid.uuid4()
        repository.create_to_do(build_entry(session_builder, todo_id))
        (created,) = raw_rows(db_path)
        old = "2000-01-01 00:00:00.000000"

        set_raw_updated_at(db_path, todo_id, old)
        before = utc_now()
        asyncio.run(service.update_todo(todo_id, TodoUpdateScheme(title="Dry dishes")))
        (row,) = raw_rows(db_path)
        assert row["title"] == "Dry dishes"
        assert before <= as_utc(row["updated_at"]) <= utc_now()

        set_raw_updated_at(db_path, todo_id, old)
        before = utc_now()
        asyncio.run(service.update_todo(todo_id, TodoUpdateScheme(done=True)))
        (row,) = raw_rows(db_path)
        assert row["done"] == 1
        assert before <= as_utc(row["updated_at"]) <= utc_now()

        set_raw_updated_at(db_path, todo_id, old)
        before = utc_now()
        asyncio.run(service.delete_todo(todo_id))
        (row,) = raw_rows(db_path)
        assert row["deleted"] == 1
        assert before <= as_utc(row["updated_at"]) <= utc_now()
        assert STORED_FORMAT.match(row["updated_at"])
        assert row["created_at"] == created["created_at"]

    def test_an_update_without_fields_leaves_updated_at_unchanged(
        self, session_builder, repository, db_path
    ):
        todo_id = uuid.uuid4()
        repository.create_to_do(build_entry(session_builder, todo_id))
        set_raw_updated_at(db_path, todo_id, "2000-01-01 00:00:00.000000")

        repository.update_to_do(todo_id, TodoUpdateScheme())

        (row,) = raw_rows(db_path)
        assert row["updated_at"] == "2000-01-01 00:00:00.000000"

    def test_a_naive_timestamp_is_refused(self, repository, db_path):
        entry = ToDoEntryData(
            id=uuid.uuid4(),
            title="Naive",
            description=None,
            created_at=datetime.datetime(2026, 10, 8, 12, 0),
            updated_at=None,
        )

        with pytest.raises(StatementError, match="timestamps must be timezone-aware"):
            repository.create_to_do(entry)
        assert raw_rows(db_path) == []


class TestDeletedRule037:
    def test_creation_path_stores_deleted_false(
        self, session_builder, repository, db_path
    ):
        entry = build_entry(session_builder, uuid.uuid4())
        assert entry.deleted is False

        repository.create_to_do(entry)

        (row,) = raw_rows(db_path)
        assert (row["deleted"], row["deleted_type"]) == (0, "integer")

    def test_model_default_for_deleted_is_false_and_stored_as_0(
        self, repository, db_path
    ):
        # Phase 4 replaced the legacy pin: the dataclass default used to be a
        # MappedColumn, and storing it failed with "no such column: deleted".
        entry = ToDoEntryData(
            id=uuid.uuid4(),
            title="No deleted flag",
            description=None,
            # Q6.6: a timezone-aware value; the model refuses naive ones.
            created_at=utc_now(),
            updated_at=None,
        )
        assert entry.deleted is False

        repository.create_to_do(entry)

        (row,) = raw_rows(db_path)
        assert (row["deleted"], row["deleted_type"]) == (0, "integer")


class TestIdBinding:
    def test_uuid_id_is_stored_as_32_lowercase_hex_digits_and_found_again(
        self, session_builder, repository, db_path
    ):
        todo_id = uuid.UUID("7C1E0000-0000-4000-8000-0000000000AB")
        repository.create_to_do(build_entry(session_builder, todo_id))

        (row,) = raw_rows(db_path)
        assert row["id"] == "7c1e00000000400080000000000000ab"
        found = repository.get_to_do_entry(todo_id)
        assert found is not None and found.id == todo_id

    @pytest.mark.parametrize(
        "spelling",
        [str, lambda value: value.hex, lambda value: str(value).upper()],
        ids=["canonical", "hex", "upper"],
    )
    def test_repository_rejects_a_string_id(
        self, spelling, session_builder, repository
    ):
        # Phase 4 replaced the legacy pin: sqlalchemy_utils.UUIDType converted
        # strings, sqlalchemy.Uuid binds uuid.UUID only. Every caller passes a
        # uuid.UUID (typed path parameters and schemas, UUIDValidator).
        todo_id = uuid.uuid4()
        repository.create_to_do(build_entry(session_builder, todo_id))

        with pytest.raises(StatementError, match="'str' object has no attribute 'hex'"):
            repository.get_to_do_entry(spelling(todo_id))
