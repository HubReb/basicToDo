"""Pins for Phase 5: behaviour it keeps and behaviour it changes on purpose.

Keeps (brief §7 Q6), pinned through Phase 5:
- RULE-024 / Q6.8: `done` accepts lax boolean spellings.
- RULE-052 / Q6.10: the last write wins; there is no version check.

Tests named "legacy" pin a behaviour that a Phase 5 commit changes on
purpose (the Q6 or SEC id is in the test's docstring). That commit replaces
the test, it does not edit it.

The routes run against the real service and repository on a file-backed
SQLite database, wired as in test_p0_contracts.py.
"""

import json
import uuid
from contextlib import contextmanager
from typing import Generator
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session, sessionmaker

from backend.app.api.api import app
from backend.app.business_logic.builders.todo_entry_builder import ToDoEntryBuilder
from backend.app.business_logic.todo_service import ToDoService
from backend.app.business_logic.validators import ValidatorFactory
from backend.app.data_access.database import Base
from backend.app.data_access.repository import ToDoRepository
from backend.app.logger import CustomLogger

ALLOWED_ORIGIN = "http://localhost:5173"


@pytest.fixture
def db_engine(tmp_path):
    engine = create_engine(
        f"sqlite:///{tmp_path / 'pins.db'}",
        connect_args={"check_same_thread": False},
    )
    Base.metadata.create_all(bind=engine)
    yield engine
    engine.dispose()


@pytest.fixture
def client(db_engine):
    session_factory = sessionmaker(
        autocommit=False, autoflush=False, bind=db_engine, expire_on_commit=False
    )

    @contextmanager
    def session_scope() -> Generator[Session, None, None]:
        session = session_factory()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    logger = CustomLogger("BehaviourPins")
    uuid_validator = ValidatorFactory.create_uuid_validator(logger)
    field_validator = ValidatorFactory.create_field_validator(logger)
    service = ToDoService(
        repository=ToDoRepository(session_scope, logger),
        logger=logger,
        input_sanitizer=ValidatorFactory.create_input_sanitizer(logger),
        uuid_validator=uuid_validator,
        field_validator=field_validator,
        builder=ToDoEntryBuilder(uuid_validator, field_validator),
    )
    with patch("backend.app.api.api.service", service):
        yield TestClient(app)


def create(client, title="Buy milk", **fields):
    todo_id = uuid.uuid4()
    response = client.post("/todo", json={"id": str(todo_id), "title": title, **fields})
    assert response.status_code == 200, response.text
    return todo_id


def stored(engine, todo_id):
    with engine.connect() as conn:
        return conn.execute(
            text('SELECT title, description, done FROM "toDo" WHERE id = :id'),
            {"id": todo_id.hex},
        ).one()


class TestKeepRule024LaxDoneCoercion:
    """Q6.8 keep: `done` takes lax boolean spellings; anything else is 422."""

    @pytest.mark.parametrize(
        "value", ["yes", "on", "1", 1, "true", "TRUE", "y", "t", 1.0]
    )
    def test_truthy_spellings_mark_done(self, client, db_engine, value):
        todo_id = create(client)

        response = client.put(f"/todo/{todo_id}", json={"done": value})

        assert response.status_code == 200
        assert response.json()["todo_entry"]["done"] is True
        assert stored(db_engine, todo_id).done == 1

    @pytest.mark.parametrize("value", ["false", 0, "off", "no"])
    def test_falsy_spellings_leave_it_open(self, client, db_engine, value):
        todo_id = create(client)

        response = client.put(f"/todo/{todo_id}", json={"done": value})

        assert response.status_code == 200
        assert response.json()["todo_entry"]["done"] is False
        assert stored(db_engine, todo_id).done == 0

    @pytest.mark.parametrize("value", ["maybe", 2, [], {}])
    def test_other_values_are_rejected(self, client, value):
        todo_id = create(client)

        assert client.put(f"/todo/{todo_id}", json={"done": value}).status_code == 422


class TestKeepRule052LastWriteWins:
    """Q6.10 keep: two edits in a row, no version check; the second one stays."""

    def test_the_later_edit_overwrites_the_earlier_one(self, client, db_engine):
        todo_id = create(client)

        first = client.put(f"/todo/{todo_id}", json={"title": "First edit"})
        second = client.put(f"/todo/{todo_id}", json={"title": "Second edit"})

        assert (first.status_code, second.status_code) == (200, 200)
        assert stored(db_engine, todo_id).title == "Second edit"


class TestLegacyBehaviourPhase5Changes:
    def test_legacy_done_true_discards_other_edits(self, client, db_engine):
        """Q6.5 (RULE-032): done:true marks done and ignores the title sent with it."""
        todo_id = create(client, title="Original")

        response = client.put(
            f"/todo/{todo_id}", json={"done": True, "title": "Renamed"}
        )

        assert response.status_code == 200
        assert tuple(stored(db_engine, todo_id))[::2] == ("Original", 1)

    def test_legacy_text_plain_body_is_a_422(self, client):
        """SEC-003: a body sent as text/plain is not parsed, and the request gets 422."""
        response = client.post(
            "/todo",
            content=json.dumps({"id": str(uuid.uuid4()), "title": "x"}),
            headers={"Content-Type": "text/plain"},
        )

        assert response.status_code == 422

    def test_legacy_any_host_is_served(self, client):
        """SEC-003: no Host check; a foreign Host header is answered normally."""
        assert client.get("/", headers={"Host": "evil.example"}).status_code == 200

    def test_legacy_cors_allows_credentials_and_every_method(self, client):
        """SEC-008: credentials allowed, methods and headers by wildcard."""
        response = client.options(
            "/todo",
            headers={
                "Origin": ALLOWED_ORIGIN,
                "Access-Control-Request-Method": "PATCH",
                "Access-Control-Request-Headers": "x-anything",
            },
        )

        assert response.status_code == 200
        assert response.headers["access-control-allow-credentials"] == "true"
        assert "PATCH" in response.headers["access-control-allow-methods"]
        assert response.headers["access-control-allow-headers"] == "x-anything"

    def test_legacy_oversized_body_is_accepted(self, client, db_engine):
        """Q8b (SEC-004): a 20,000-byte body is read and processed."""
        todo_id = uuid.uuid4()
        body = json.dumps({"id": str(todo_id), "title": "Padded"}).encode()

        response = client.post(
            "/todo",
            content=body + b" " * (20000 - len(body)),
            headers={"Content-Type": "application/json"},
        )

        assert response.status_code == 200
        assert stored(db_engine, todo_id).title == "Padded"


class TestPhase5Behaviour:
    """What Phase 5 changed, replacing the legacy pins above."""

    def test_nul_in_a_title_is_rejected(self, client, db_engine):
        """Q6.2 (RULE-021): NUL is a control character; nothing is stored."""
        response = client.post(
            "/todo", json={"id": str(uuid.uuid4()), "title": "a\x00" + "b" * 300}
        )

        assert response.status_code == 422
        with db_engine.connect() as conn:
            assert conn.execute(text('SELECT COUNT(*) FROM "toDo"')).scalar() == 0

    def test_put_title_null_is_a_422(self, client, db_engine):
        """Q6.3: an explicit null title is a validation error; the title stays."""
        todo_id = create(client, title="Kept")

        response = client.put(f"/todo/{todo_id}", json={"title": None})

        assert response.status_code == 422
        assert stored(db_engine, todo_id).title == "Kept"
