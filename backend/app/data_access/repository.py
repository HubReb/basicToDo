"""A ToDo data class"""
import datetime
import uuid
from typing import Any, Generator, List
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from backend.app.data_access.database import get_db
from backend.app import models
from backend.app.models.todo import ToDoEntryData


class ToDoRepository:
    """Repository for ToDos"""

    def __init__(self, db: Generator[Session, Any, None] = get_db):
        """Initialize repository"""
        self.database = get_db

    def add_to_do(
        self, new_to_do_entry: models.todo.ToDoEntryData
    ) -> None | IntegrityError | Exception:
        """Add a new ToDo entry."""
        todo_entry = ToDoEntryData(id=new_to_do_entry.id, title=new_to_do_entry.title, description=new_to_do_entry.description,
                               created_at=datetime.datetime.now(), updated_at=None, done=False, deleted=False)
        try:
            for val in self.database():
                session = val
                break
            if not session:
                raise EnvironmentError("Failed to create session")
            session.add(todo_entry)
            session.commit()
            session.refresh(todo_entry)
        except IntegrityError as e:
            session.rollback()
            raise e
        except Exception as e:
            session.rollback()
            raise e
        return None

    def delete_to_do(self, to_do_id: uuid.UUID) -> None | ValueError | Exception:
        """Delete a ToDo."""
        for val in self.database():
            session = val
            break
        if not session:
            raise EnvironmentError("Failed to create session")
        try:
            to_do_query = session.query(models.todo.ToDoEntryData).filter_by(
                id=to_do_id
            )
            if not to_do_query.first():
                raise ValueError(f"No ToDo entry with id {to_do_id} found.")
            to_do_query.delete(synchronize_session=False)
            session.commit()
            return None
        except Exception as e:
            session.rollback()
            raise e

    def update_to_do(
        self, to_do_id: uuid.UUID, update_data: dict[str, Any]
    ) -> models.todo.ToDoEntryData | IntegrityError | Exception:
        """Update an existing ToDo entry."""
        for val in self.database():
            session = val
            break
        if not session:
            raise EnvironmentError("Failed to create session")
        try:
            to_do_query = session.query(models.todo.ToDoEntryData).filter_by(
                id=to_do_id
            )
            to_do_entry = to_do_query.first()
            if not to_do_entry:
                raise ValueError(f"No entry with id {to_do_id} found.")
            to_do_entry.update(update_data)
            session.commit()
            session.refresh(to_do_entry)
            return to_do_entry
        except IntegrityError as e:
            session.rollback()
            raise e
        except Exception as e:
            session.rollback()
            raise e

    def get_to_do_entry(self, to_do_entry_id: uuid.UUID) -> models.todo.ToDoEntryData | ValueError:
        """Get an ToDo entry."""
        for val in self.database():
            session = val
            break
        if not session:
            raise EnvironmentError("Failed to create session")
        to_do_query = session.query(models.todo.ToDoEntryData).filter_by(
            id=to_do_entry_id
        )
        to_do_entry = to_do_query.first()
        if not to_do_entry:
            raise ValueError(f"No entry with id {to_do_entry_id}.")
        return to_do_entry

    def get_all_to_do_entries(
        self, limit: int = 10, page: int = 1
    ) -> List[models.todo.ToDoEntryData]:
        """Search all ToDo entries for the search string."""
        skip = (page - 1) * limit
        for val in self.database():
            session = val
            break
        if not session:
            raise EnvironmentError("Failed to create session")
        to_do_entries = (
            session.query(models.todo.ToDoEntryData).limit(limit).offset(skip).all()
        )
        return to_do_entries