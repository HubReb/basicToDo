"""P0 contract tests: identity and deletion semantics.

RULE-008: a ToDo id is a client-supplied UUID and must be unique; a
duplicate, including the id of a soft-deleted todo, is rejected with 409.
RULE-031: delete is a soft delete; the row is kept, flagged deleted and
cannot be restored.

Unlike the other API tests, nothing is mocked here: the routes run against
the real service, repository and a file-backed SQLite database, wired the
same way as backend.app.factory.create_todo_service.
"""
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


@pytest.fixture
def db_engine(tmp_path):
    """File-backed SQLite, so every thread of the TestClient sees one database."""
    engine = create_engine(
        f"sqlite:///{tmp_path / 'p0_contracts.db'}",
        connect_args={"check_same_thread": False},
    )
    Base.metadata.create_all(bind=engine)
    yield engine
    engine.dispose()


@pytest.fixture
def client(db_engine):
    """TestClient whose routes use a real service on db_engine."""
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

    logger = CustomLogger("P0Contracts")
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


def stored_rows(engine) -> dict[str, bool]:
    """All rows of the toDo table as {id hex: deleted}, read past the ORM."""
    with engine.connect() as conn:
        rows = conn.execute(text('SELECT id, deleted FROM "toDo"')).all()
    return {str(row.id).replace("-", ""): bool(row.deleted) for row in rows}


def create(client, todo_id, title="Buy milk"):
    return client.post("/todo", json={"id": str(todo_id), "title": title})


class TestRule008ClientSuppliedUniqueId:
    """RULE-008: client-supplied UUID id, duplicates rejected with 409."""

    def test_create_with_new_uuid_echoes_the_id(self, client, db_engine):
        todo_id = uuid.uuid4()

        response = create(client, todo_id)

        assert response.status_code == 200
        assert response.json()["todo_entry"]["id"] == str(todo_id)
        assert stored_rows(db_engine) == {todo_id.hex: False}

    def test_same_id_again_is_rejected_with_409(self, client, db_engine):
        todo_id = uuid.uuid4()
        assert create(client, todo_id).status_code == 200

        response = create(client, todo_id, title="Buy bread")

        assert response.status_code == 409
        assert response.json() == {"detail": "ToDo already exists"}
        assert stored_rows(db_engine) == {todo_id.hex: False}

    def test_recreating_a_soft_deleted_id_is_rejected_with_409(self, client, db_engine):
        todo_id = uuid.uuid4()
        assert create(client, todo_id).status_code == 200
        assert client.delete(f"/todo/{todo_id}").status_code == 200

        response = create(client, todo_id, title="Buy bread")

        assert response.status_code == 409
        assert response.json() == {"detail": "ToDo already exists"}
        assert stored_rows(db_engine) == {todo_id.hex: True}

    @pytest.mark.parametrize(
        "payload",
        [
            {"title": "Buy milk"},
            {"id": "not-a-uuid", "title": "Buy milk"},
            {"id": "", "title": "Buy milk"},
            {"id": None, "title": "Buy milk"},
        ],
        ids=["missing", "malformed", "empty", "null"],
    )
    def test_missing_or_malformed_id_is_rejected_with_422(
        self, client, db_engine, payload
    ):
        response = client.post("/todo", json=payload)

        assert response.status_code == 422
        assert response.json()["detail"][0]["loc"] == ["body", "id"]
        assert stored_rows(db_engine) == {}


class TestRule031SoftDelete:
    """RULE-031: delete keeps the row, flags it deleted, and cannot be undone."""

    def test_delete_keeps_the_row_flagged_deleted(self, client, db_engine):
        todo_id = uuid.uuid4()
        assert create(client, todo_id).status_code == 200

        response = client.delete(f"/todo/{todo_id}")

        assert response.status_code == 200
        assert response.json()["success"] is True
        assert response.json()["message"] == "Deleted successfully"
        assert stored_rows(db_engine) == {todo_id.hex: True}

    def test_second_delete_returns_404(self, client, db_engine):
        todo_id = uuid.uuid4()
        assert create(client, todo_id).status_code == 200
        assert client.delete(f"/todo/{todo_id}").status_code == 200

        response = client.delete(f"/todo/{todo_id}")

        assert response.status_code == 404
        assert response.json() == {"detail": "ToDo not found"}
        assert stored_rows(db_engine) == {todo_id.hex: True}

    def test_deleted_todo_is_invisible_to_get_update_and_list(self, client, db_engine):
        kept_id, deleted_id = uuid.uuid4(), uuid.uuid4()
        assert create(client, kept_id, title="Keep me").status_code == 200
        assert create(client, deleted_id, title="Remove me").status_code == 200
        assert client.delete(f"/todo/{deleted_id}").status_code == 200

        assert client.get(f"/todo/{deleted_id}").status_code == 404
        assert (
            client.put(f"/todo/{deleted_id}", json={"title": "Changed"}).status_code
            == 404
        )
        listed = client.get("/todo").json()
        assert [entry["id"] for entry in listed["todo_entries"]] == [str(kept_id)]
        assert listed["results"] == 1

    def test_there_is_no_restore_path(self, client, db_engine):
        todo_id = uuid.uuid4()
        assert create(client, todo_id).status_code == 200
        assert client.delete(f"/todo/{todo_id}").status_code == 200

        response = client.put(f"/todo/{todo_id}", json={"deleted": False})

        assert response.status_code == 404
        assert stored_rows(db_engine) == {todo_id.hex: True}

    def test_row_count_is_unchanged_by_delete(self, client, db_engine):
        ids = [uuid.uuid4() for _ in range(3)]
        for todo_id in ids:
            assert create(client, todo_id).status_code == 200

        assert client.delete(f"/todo/{ids[1]}").status_code == 200

        rows = stored_rows(db_engine)
        assert len(rows) == 3
        assert rows == {ids[0].hex: False, ids[1].hex: True, ids[2].hex: False}
