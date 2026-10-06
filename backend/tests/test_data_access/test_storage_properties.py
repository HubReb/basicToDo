"""Storage round-trip properties of the toDo table.

What goes in through the ORM must come out unchanged, and must be stored in
the format the legacy code writes: ids as 32 lowercase hex digits, timestamps
as text with microseconds, booleans as 0/1. Like the characterization tests
next to this module, these run unchanged against the legacy dual mapping and
against the declarative model that replaces it in Phase 4.

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
from sqlalchemy.orm import Session, sessionmaker

from backend.app.data_access.database import Base
from backend.app.data_access.repository import ToDoRepository
from backend.app.logger import CustomLogger
from backend.app.models.todo import ToDoEntryData

PROPERTY_SETTINGS = settings(deadline=None, derandomize=True, database=None)

FIXED_CREATED_AT = datetime.datetime(2026, 10, 3, 14, 5, 0, 123456)

# Fixed UTC offsets: aware values without DST gaps or folds.
utc_offsets = st.timedeltas(
    min_value=-datetime.timedelta(hours=23, minutes=59),
    max_value=datetime.timedelta(hours=23, minutes=59),
).map(
    lambda delta: datetime.timezone(
        datetime.timedelta(minutes=delta // datetime.timedelta(minutes=1))
    )
)


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
@given(created_at=st.datetimes(), updated_at=st.datetimes())
def test_naive_timestamps_are_stored_as_text_and_read_back_exactly(
    storage, created_at, updated_at
):
    storage.clear()
    todo_id = uuid.uuid4()
    storage.repository.create_to_do(
        entry_for(todo_id, created_at=created_at, updated_at=updated_at)
    )

    assert storage.raw('SELECT created_at, updated_at FROM "toDo"') == [
        (stored_text(created_at), stored_text(updated_at))
    ]
    entry = storage.load(todo_id)
    assert (entry.created_at, entry.updated_at) == (created_at, updated_at)


@PROPERTY_SETTINGS
@given(created_at=st.datetimes(timezones=utc_offsets))
def test_aware_timestamps_lose_their_offset_and_keep_the_wall_clock(
    storage, created_at
):
    storage.clear()
    todo_id = uuid.uuid4()
    storage.repository.create_to_do(entry_for(todo_id, created_at=created_at))

    assert storage.raw('SELECT created_at FROM "toDo"') == [(stored_text(created_at),)]
    entry = storage.load(todo_id)
    assert entry.created_at == created_at.replace(tzinfo=None)
    assert entry.created_at is not None and entry.created_at.tzinfo is None


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
