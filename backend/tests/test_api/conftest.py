"""API test fixtures, shared by the modules of this directory."""

from contextlib import contextmanager
from typing import Generator
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from backend.app.api.api import app
from backend.app.business_logic.builders.todo_entry_builder import ToDoEntryBuilder
from backend.app.business_logic.todo_service import ToDoService
from backend.app.business_logic.validators import ValidatorFactory
from backend.app.data_access.database import Base
from backend.app.data_access.repository import ToDoRepository
from backend.app.logger import CustomLogger

# Registered here, so the test modules use them without importing them.
from backend.tests.test_api.test_setup_for_api_endpoins import (  # noqa: F401
    client,
    created_todo,
    mock_service,
)


@pytest.fixture
def real_db_engine(tmp_path):
    """File-backed SQLite, so every thread of the TestClient sees one database."""
    engine = create_engine(
        f"sqlite:///{tmp_path / 'api.db'}", connect_args={"check_same_thread": False}
    )
    Base.metadata.create_all(bind=engine)
    yield engine
    engine.dispose()


@pytest.fixture
def real_client(real_db_engine):
    """TestClient whose routes use the real service and repository on real_db_engine."""
    session_factory = sessionmaker(
        autocommit=False, autoflush=False, bind=real_db_engine, expire_on_commit=False
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

    logger = CustomLogger("ApiTests")
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
