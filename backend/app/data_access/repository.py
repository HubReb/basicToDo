import uuid
from abc import ABC, abstractmethod
from typing import Callable, List, Optional, cast

from sqlalchemy.exc import IntegrityError

from backend.app.logger import CustomLogger
from backend.app.models.todo import ToDoEntryData
from backend.app.schemas.data_schemes.update_todo_schema import TodoUpdateScheme


class ToDoRepositoryInterface(ABC):
    @abstractmethod
    def create_to_do(self, entry: ToDoEntryData) -> None:
        pass

    @abstractmethod
    def delete_to_do(self, entry_id: uuid.UUID) -> bool:
        pass

    @abstractmethod
    def hard_delete_to_do(self, to_do_id: uuid.UUID) -> bool:
        pass

    @abstractmethod
    def update_to_do(self, entry_id: uuid.UUID, data: TodoUpdateScheme) -> Optional[ToDoEntryData]:
        pass

    @abstractmethod
    def get_to_do_entry(self, entry_id: uuid.UUID) -> Optional[ToDoEntryData]:
        pass

    @abstractmethod
    def get_all_to_do_entries(self, limit: int = 10, page: int = 1) -> List[ToDoEntryData]:
        pass


class ToDoRepository(ToDoRepositoryInterface):
    """Repository for ToDos (SQL-injection-safe)"""

    def __init__(self, session_manager: Callable, logger: CustomLogger):
        self.session_manager = session_manager
        self.logger = logger

    def create_to_do(self, entry: ToDoEntryData) -> None:
        with self.session_manager() as session:
            try:
                session.add(entry)
            except IntegrityError as e:
                self.logger.error("Integrity error during insert: %s", e)
                raise

    def delete_to_do(self, entry_id: uuid.UUID) -> bool:
        entry = self.get_to_do_entry(entry_id)
        if not entry:
            return False
        with self.session_manager() as session:
            entry.deleted = True
            session.merge(entry)
        return True

    def hard_delete_to_do(self, to_do_id: uuid.UUID) -> bool:
        entry = self.get_to_do_entry(to_do_id)
        if not entry:
            return False
        with self.session_manager() as session:
            session.delete(entry)
        return True

    def update_to_do(self, entry_id: uuid.UUID, data: TodoUpdateScheme) -> Optional[ToDoEntryData]:
        with self.session_manager() as session:
            entry: Optional[ToDoEntryData] = session.query(ToDoEntryData).filter(
                ToDoEntryData.id == entry_id, ToDoEntryData.deleted.is_(False)
            ).first()
            if not entry:
                return None
            for key, value in data.model_dump(exclude_unset=True).items():
                setattr(entry, key, value)
            try:
                session.merge(entry)
            except IntegrityError as e:
                self.logger.error("Integrity error during update: %s", e)
                raise
            return entry

    def get_to_do_entry(self, entry_id: uuid.UUID) -> Optional[ToDoEntryData]:
        with self.session_manager() as session:
            return cast(Optional[ToDoEntryData], session.query(ToDoEntryData).filter(
                ToDoEntryData.id == entry_id, ToDoEntryData.deleted.is_(False)
            ).first())

    def get_all_to_do_entries(self, limit: int = 10, page: int = 1) -> List[ToDoEntryData]:
        skip = (page - 1) * limit
        with self.session_manager() as session:
            return cast(List[ToDoEntryData], session.query(ToDoEntryData).filter(
                ToDoEntryData.deleted.is_(False)
            ).offset(skip).limit(limit).all())