"""A ToDo data class"""
import uuid
from contextlib import _GeneratorContextManager
from typing import Any, List, Optional

from sqlalchemy.exc import IntegrityError

from backend.app.data_access.database import get_db_session
from backend.app.models.todo import ToDoEntryData
from backend.app.schemas.todo import TodoUpdateEntry


class ToDoRepository:
    """Repository for ToDos"""

    def __init__(self, get_db_session: _GeneratorContextManager[Any] = get_db_session):
        """Initialize repository"""
        self.database = get_db_session

    def create_to_do(
        self, entry: ToDoEntryData
    ) -> None:
        """Create a new ToDo entry."""
        with self.database() as session:
            try:
                session.add(entry)
                session.commit()
            except IntegrityError as e:
                session.rollback()
                raise e
            except Exception as e:
                session.rollback()
                raise e
        return None

    def delete_to_do(self, entry_id: uuid.UUID) -> bool:
        """Soft delete a ToDo entry."""
        entry = self.get_to_do_entry(entry_id)
        if not entry:
            return False
        with self.database() as session:
            try:
                entry.deleted = True
                session.add(entry)
                session.commit()
                return True
            except Exception as e:
                session.rollback()
                raise e

    def hard_delete_to_do(self, to_do_id: uuid.UUID) -> bool:
        """Hard delete a ToDo entry."""
        to_do = self.get_to_do_entry(to_do_id)
        if not to_do:
            return False
        with self.database() as session:
            session.delete(to_do)
            session.commit()
        return True



    def update_to_do(
            self, entry_id: uuid.UUID, data: TodoUpdateEntry
    ) -> Optional[ToDoEntryData]:
        """Update an existing ToDo entry."""
        with self.database() as session:
            entry = self.get_to_do_entry(entry_id)
            if not entry:
                return None
            update_data = data.model_dump(exclude_unset=True)
            for key, value in update_data.items():
                setattr(entry, key, value)
            try:
                session.add(entry)
                session.commit()
            except IntegrityError as e:
                session.rollback()
                raise e
            except Exception as e:
                session.rollback()
                raise e
        return entry

    def get_to_do_entry(self, entry_id: uuid.UUID) -> Optional[ToDoEntryData]:
        """Get an ToDo entry."""
        with self.database() as session:
            to_do_query = session.query(ToDoEntryData).filter_by(
                id=entry_id
            ).filter_by(deleted=False)
            to_do_entry = to_do_query.first()
            if not to_do_entry:
                return None
        return to_do_entry

    def get_all_to_do_entries(
        self, limit: int = 10, page: int = 1
    ) -> List[ToDoEntryData]:
        """Search all ToDo entries for the search string."""
        skip = (page - 1) * limit
        with self.database() as session:
            to_do_entries = (
                session.query(ToDoEntryData).filter_by(deleted=False).limit(limit).offset(skip).all()
            )
        return to_do_entries