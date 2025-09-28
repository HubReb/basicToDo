"""A ToDo data class"""
import datetime
import uuid
from contextlib import _GeneratorContextManager
from typing import Any, List
from sqlalchemy.exc import IntegrityError

from backend.app.data_access.database import get_db_session
from backend.app.models.todo import ToDoEntryData


class ToDoRepository:
    """Repository for ToDos"""

    def __init__(self, get_db_session: _GeneratorContextManager[Any] = get_db_session):
        """Initialize repository"""
        self.database = get_db_session

    def add_to_do(
        self, entry: ToDoEntryData
    ) -> None:
        """Add a new ToDo entry."""
        todo_entry = ToDoEntryData(id=entry.id, title=entry.title, description=entry.description,
                                   created_at=datetime.datetime.now(), updated_at=None, done=False, deleted=False)
        with self.database() as session:
            try:
                session.add(todo_entry)
                session.commit()
            except IntegrityError as e:
                session.rollback()
                raise e
            except Exception as e:
                session.rollback()
                raise e
        return None

    def delete_to_do(self, entry_id: uuid.UUID) -> None:
        """Delete a ToDo."""
        with self.database() as session:
            try:
                to_do_query = session.query(ToDoEntryData).filter_by(id=entry_id)
                if not to_do_query.first():
                    raise ValueError(f"No ToDo entry with id {entry_id} found.")
                to_do_query.delete(synchronize_session=False)
                session.commit()
            except Exception as e:
                session.rollback()
                raise e
        return None

    def update_to_do(
        self, entry_id: uuid.UUID, data: dict[str, Any]
    ) -> ToDoEntryData:
        """Update an existing ToDo entry."""
        with self.database() as session:
            try:
                to_do_query = session.query(ToDoEntryData).filter_by(
                    id=entry_id
                )
                to_do_entry = to_do_query.first()
                if not to_do_entry:
                    raise ValueError(f"No entry with id {entry_id} found.")
                to_do_entry.update(data)
                session.commit()

            except IntegrityError as e:
                session.rollback()
                raise e
            except Exception as e:
                session.rollback()
                raise e
        return to_do_entry

    def get_to_do_entry(self, entry_id: uuid.UUID) -> ToDoEntryData:
        """Get an ToDo entry."""
        with self.database() as session:
            to_do_query = session.query(ToDoEntryData).filter_by(
                id=entry_id
            )
            to_do_entry = to_do_query.first()
            if not to_do_entry:
                raise ValueError(f"No entry with id {entry_id}.")
        return to_do_entry

    def get_all_to_do_entries(
        self, limit: int = 10, page: int = 1
    ) -> List[ToDoEntryData]:
        """Search all ToDo entries for the search string."""
        skip = (page - 1) * limit
        with self.database() as session:
            to_do_entries = (
                session.query(ToDoEntryData).limit(limit).offset(skip).all()
            )
        return to_do_entries