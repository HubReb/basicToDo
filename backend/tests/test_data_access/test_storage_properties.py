"""Storage round-trip properties of the toDo table.

What goes in through the ORM must come out unchanged, and must be stored in
the format the legacy code writes: ids as 32 lowercase hex digits, timestamps
as text with microseconds, booleans as 0/1. Like the characterization tests
next to this module, these ran unchanged against the legacy dual mapping and
against the declarative model that replaced it in Phase 4. Q6.6 (Phase 5)
made timestamps UTC: an aware value is stored as its UTC wall clock and read
back equal, a naive one is refused. The two legacy timestamp properties
(naive values stored as given, aware values stored with their own wall clock
and read back naive) were replaced, not edited.

Hypothesis runs derandomized and without its example database, so every run
draws the same examples and the per-test outcome table stays comparable.
"""

import datetime
import sqlite3
import uuid
from contextlib import contextmanager
from typing import Generator

import pytest
from hypothesis import example, given, settings
from hypothesis import strategies as st
from sqlalchemy import create_engine
from sqlalchemy.exc import StatementError
from sqlalchemy.orm import Session, sessionmaker

from backend.app.data_access.database import Base
from backend.app.data_access.repository import ToDoRepository
from backend.app.logger import CustomLogger
from backend.app.models.todo import ToDoEntryData

PROPERTY_SETTINGS = settings(deadline=None, derandomize=True, database=None)

# Timezone-aware since Q6.6: the model refuses naive timestamps.
FIXED_CREATED_AT = datetime.datetime(
    2026, 10, 3, 14, 5, 0, 123456, tzinfo=datetime.timezone.utc
)

# Fixed UTC offsets: aware values without DST gaps or folds.
utc_offsets = st.timedeltas(
    min_value=-datetime.timedelta(hours=23, minutes=59),
    max_value=datetime.timedelta(hours=23, minutes=59),
).map(
    lambda delta: datetime.timezone(
        datetime.timedelta(minutes=delta // datetime.timedelta(minutes=1))
    )
)

# A day inside datetime's range on both ends, so that the UTC value exists.
AWARE_RANGE = {
    "min_value": datetime.datetime(1, 1, 2),
    "max_value": datetime.datetime(9999, 12, 30, 23, 59, 59, 999999),
}


class Storage:
    """One SQLite file for a whole property; every example starts from an empty table."""

    def __init__(self, path):
        self.path = path
        self.engine = create_engine(f"sqlite:///{path}")
        Base.metadata.create_all(bind=self.engine)
        self.session_local = sessionmaker(
            autocommit=False, autoflush=False, bind=self.engine, expire_on_commit=False
        )
        self.repository = ToDoRepository(
            self.session_scope, CustomLogger("StorageProperties")
        )

    @contextmanager
    def session_scope(self) -> Generator[Session, None, None]:
        session = self.session_local()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def clear(self) -> None:
        self.raw('DELETE FROM "toDo"')

    def raw(self, sql: str, *params) -> list[tuple]:
        connection = sqlite3.connect(self.path)
        try:
            rows = connection.execute(sql, params).fetchall()
            connection.commit()
        finally:
            connection.close()
        return rows

    def load(self, todo_id: uuid.UUID) -> ToDoEntryData:
        """Read back through the mapping, including soft-deleted rows."""
        with self.session_local() as session:
            entry = session.get(ToDoEntryData, todo_id)
        assert entry is not None
        return entry


@pytest.fixture(scope="module")
def storage(tmp_path_factory) -> Generator[Storage, None, None]:
    storage = Storage(tmp_path_factory.mktemp("properties") / "storage.db")
    yield storage
    storage.engine.dispose()


def entry_for(todo_id: uuid.UUID, **fields) -> ToDoEntryData:
    values = {
        "title": "Round trip",
        "description": None,
        "created_at": FIXED_CREATED_AT,
        "updated_at": None,
        "deleted": False,
        "done": False,
    }
    values.update(fields)
    return ToDoEntryData(id=todo_id, **values)


def stored_text(value: datetime.datetime) -> str:
    """The text SQLAlchemy's SQLite DATETIME writes: the wall clock, with microseconds."""
    return (
        f"{value.year:04d}-{value.month:02d}-{value.day:02d} "
        f"{value.hour:02d}:{value.minute:02d}:{value.second:02d}.{value.microsecond:06d}"
    )


@PROPERTY_SETTINGS
@given(todo_id=st.uuids(allow_nil=True))
@example(todo_id=uuid.UUID(int=0))
@example(todo_id=uuid.UUID(int=2**128 - 1))
def test_any_uuid_is_stored_as_its_hex_and_read_back_equal(storage, todo_id):
    storage.clear()
    storage.repository.create_to_do(entry_for(todo_id))

    assert storage.raw('SELECT id FROM "toDo"') == [(todo_id.hex,)]
    found = storage.repository.get_to_do_entry(todo_id)
    assert found is not None and found.id == todo_id


@PROPERTY_SETTINGS
@given(created_at=st.datetimes())
def test_naive_timestamps_are_refused(storage, created_at):
    storage.clear()
    entry = entry_for(uuid.uuid4(), created_at=created_at)

    with pytest.raises(StatementError, match="timestamps must be timezone-aware"):
        storage.repository.create_to_do(entry)
    assert storage.raw('SELECT count(*) FROM "toDo"') == [(0,)]


@PROPERTY_SETTINGS
@given(
    created_at=st.datetimes(timezones=utc_offsets, **AWARE_RANGE),
    updated_at=st.datetimes(timezones=utc_offsets, **AWARE_RANGE),
)
@example(
    created_at=datetime.datetime(
        2026, 1, 1, 0, 30, tzinfo=datetime.timezone(datetime.timedelta(hours=1))
    ),
    updated_at=datetime.datetime(2026, 1, 1, tzinfo=datetime.timezone.utc),
)
def test_aware_timestamps_are_stored_as_utc_and_read_back_equal(
    storage, created_at, updated_at
):
    storage.clear()
    todo_id = uuid.uuid4()
    storage.repository.create_to_do(
        entry_for(todo_id, created_at=created_at, updated_at=updated_at)
    )

    utc = datetime.timezone.utc
    assert storage.raw('SELECT created_at, updated_at FROM "toDo"') == [
        (
            stored_text(created_at.astimezone(utc)),
            stored_text(updated_at.astimezone(utc)),
        )
    ]
    entry = storage.load(todo_id)
    assert (entry.created_at, entry.updated_at) == (created_at, updated_at)
    assert entry.created_at is not None and entry.created_at.tzinfo is utc


@PROPERTY_SETTINGS
@given(deleted=st.booleans(), done=st.booleans())
def test_flags_are_stored_as_0_or_1_and_read_back_as_booleans(storage, deleted, done):
    storage.clear()
    todo_id = uuid.uuid4()
    storage.repository.create_to_do(entry_for(todo_id, deleted=deleted, done=done))

    assert storage.raw(
        'SELECT deleted, done, typeof(deleted), typeof(done) FROM "toDo"'
    ) == [(int(deleted), int(done), "integer", "integer")]
    entry = storage.load(todo_id)
    assert (entry.deleted, entry.done) == (deleted, done)
