"""Q6.2 and Q6.3: the rules for title and description, and their status codes.

Titles: no Unicode control character (Cc), tab and newline included; no
unpaired surrogate (Cs); stripped; not blank; at most 255 code points.
Descriptions: the same, except that tab, line feed and carriage return
are allowed. Control characters and surrogates are checked before
stripping. Every violation is a 422 and stores nothing; only a duplicate
id is a 409. The routes run against the real service and repository on a
file-backed SQLite database.
"""

import json
import unicodedata
import uuid
from contextlib import contextmanager
from typing import Generator
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient
from hypothesis import example, given, settings
from hypothesis import strategies as st
from pydantic import ValidationError
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session, sessionmaker

from backend.app.api.api import app
from backend.app.business_logic.builders.todo_entry_builder import ToDoEntryBuilder
from backend.app.business_logic.todo_service import ToDoService
from backend.app.business_logic.validators import ValidatorFactory
from backend.app.data_access.database import Base
from backend.app.data_access.repository import ToDoRepository
from backend.app.logger import CustomLogger
from backend.app.schemas.data_schemes.create_todo_schema import ToDoCreateScheme

FOUR_BYTES = "\U0001f600"


@pytest.fixture
def db_engine(tmp_path):
    engine = create_engine(
        f"sqlite:///{tmp_path / 'rules.db'}", connect_args={"check_same_thread": False}
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

    logger = CustomLogger("ValidationRules")
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


def count(engine) -> int:
    with engine.connect() as conn:
        return conn.execute(text('SELECT COUNT(*) FROM "toDo"')).scalar()


def stored(engine, todo_id):
    with engine.connect() as conn:
        return conn.execute(
            text('SELECT title, description FROM "toDo" WHERE id = :id'),
            {"id": todo_id.hex},
        ).one()


def post(client, title, description=None):
    body = {"id": str(uuid.uuid4()), "title": title}
    if description is not None:
        body["description"] = description
    return client.post("/todo", json=body)


class TestLength:
    def test_255_four_byte_characters_pass(self, client, db_engine):
        todo_id = uuid.uuid4()
        response = client.post(
            "/todo",
            json={
                "id": str(todo_id),
                "title": FOUR_BYTES * 255,
                "description": FOUR_BYTES * 255,
            },
        )

        assert response.status_code == 200
        assert tuple(map(len, stored(db_engine, todo_id))) == (255, 255)

    @pytest.mark.parametrize("field", ["title", "description"])
    def test_256_characters_are_a_422(self, client, db_engine, field):
        fields = {"title": "ok", field: FOUR_BYTES * 256}

        response = post(client, **fields)

        assert response.status_code == 422
        assert count(db_engine) == 0

    def test_the_length_is_counted_after_stripping(self, client):
        assert post(client, " " + "s" * 255 + " ").status_code == 200

    def test_an_over_length_edit_is_a_422_not_a_500(self, client, db_engine):
        todo_id = uuid.uuid4()
        client.post("/todo", json={"id": str(todo_id), "title": "Short"})

        response = client.put(f"/todo/{todo_id}", json={"title": "t" * 256})

        assert response.status_code == 422
        assert stored(db_engine, todo_id).title == "Short"


class TestControlCharacters:
    @pytest.mark.parametrize(
        "char", ["\x00", "\t", "\n", "\r", "\x1c", "\x1f", "\x7f", "\x85"]
    )
    @pytest.mark.parametrize("where", ["start", "middle", "end"])
    def test_a_title_with_a_control_character_is_a_422(
        self, client, db_engine, char, where
    ):
        title = {"start": char + "ab", "middle": "a" + char + "b", "end": "ab" + char}[
            where
        ]

        assert post(client, title).status_code == 422
        assert count(db_engine) == 0

    def test_a_description_keeps_tab_and_line_breaks(self, client, db_engine):
        todo_id = uuid.uuid4()
        response = client.post(
            "/todo",
            json={"id": str(todo_id), "title": "Lines", "description": "a\tb\r\nc\nd"},
        )

        assert response.status_code == 200
        assert stored(db_engine, todo_id).description == "a\tb\r\nc\nd"

    @pytest.mark.parametrize("char", ["\x00", "\x1c", "\x7f", "\x85", "\x0b"])
    def test_a_description_with_another_control_character_is_a_422(
        self, client, db_engine, char
    ):
        assert post(client, "ok", "a" + char + "b").status_code == 422
        assert count(db_engine) == 0

    @pytest.mark.parametrize("field", ["title", "description"])
    def test_an_unpaired_surrogate_is_a_422(self, client, db_engine, field):
        body = {"id": str(uuid.uuid4()), "title": "ok", field: "a\ud800b"}

        response = client.post(
            "/todo",
            content=json.dumps(body),  # ensure_ascii sends it as \\ud800
            headers={"Content-Type": "application/json"},
        )

        assert response.status_code == 422
        assert count(db_engine) == 0


class TestStatusCodes:
    @pytest.mark.parametrize("title", ["", "   "], ids=["empty", "whitespace"])
    def test_a_blank_title_is_a_422_on_create_and_edit(self, client, title):
        todo_id = uuid.uuid4()
        client.post("/todo", json={"id": str(todo_id), "title": "Kept"})

        assert post(client, title).status_code == 422
        assert client.put(f"/todo/{todo_id}", json={"title": title}).status_code == 422

    def test_put_done_null_is_a_422(self, client):
        todo_id = uuid.uuid4()
        client.post("/todo", json={"id": str(todo_id), "title": "Open"})

        assert client.put(f"/todo/{todo_id}", json={"done": None}).status_code == 422

    def test_put_description_null_clears_it(self, client, db_engine):
        todo_id = uuid.uuid4()
        client.post(
            "/todo", json={"id": str(todo_id), "title": "Note", "description": "x"}
        )

        response = client.put(f"/todo/{todo_id}", json={"description": None})

        assert response.status_code == 200
        assert stored(db_engine, todo_id).description is None

    def test_only_a_duplicate_id_is_a_409(self, client):
        todo_id = str(uuid.uuid4())
        client.post("/todo", json={"id": todo_id, "title": "First"})

        response = client.post("/todo", json={"id": todo_id, "title": "Again"})

        assert response.status_code == 409


def title_is_valid(value: str) -> bool:
    """The rule, written out independently of the implementation."""
    if any(unicodedata.category(c) in ("Cc", "Cs") for c in value):
        return False
    return 1 <= len(value.strip()) <= 255


@settings(deadline=None, derandomize=True, database=None, max_examples=300)
@given(
    st.text(
        alphabet=st.characters(categories=("Cc", "Cs", "Ll", "Lu", "Zs", "So", "Nd")),
        max_size=270,
    )
)
@example("x" * 255)
@example("x" * 256)
@example(" " + "x" * 255 + " ")
@example("ab\x1c")
def test_the_title_rule_holds_for_any_text(value):
    """Brief §6: the schema accepts exactly the titles the rule allows."""
    try:
        ToDoCreateScheme(id=uuid.uuid4(), title=value)
        accepted = True
    except ValidationError:
        accepted = False

    assert accepted == title_is_valid(value)
