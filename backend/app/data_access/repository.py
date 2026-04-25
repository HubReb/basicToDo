import datetime
import uuid
from abc import ABC, abstractmethod
from collections.abc import Callable
from typing import List, Optional

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError

from backend.app.data_access.database import ToDoORM
from backend.app.logger import CustomLogger
from backend.app.schemas.data_schemes.update_todo_schema import TodoUpdateScheme


class ToDoRepositoryInterface(ABC):
    @abstractmethod
    async def create_to_do(self, entry: ToDoORM) -> None:
        pass

    @abstractmethod
    async def delete_to_do(self, entry_id: uuid.UUID) -> bool:
        pass

    @abstractmethod
    async def hard_delete_to_do(self, to_do_id: uuid.UUID) -> bool:
        pass

    @abstractmethod
    async def update_to_do(
        self, entry_id: uuid.UUID, data: TodoUpdateScheme
    ) -> Optional[ToDoORM]:
        pass

    @abstractmethod
    async def get_to_do_entry(self, entry_id: uuid.UUID) -> Optional[ToDoORM]:
        pass

    @abstractmethod
    async def get_all_to_do_entries(
        self, limit: int = 10, page: int = 1
    ) -> List[ToDoORM]:
        pass

    @abstractmethod
    async def count_active(self) -> int:
        pass

    @abstractmethod
    async def get_deleted_entries(
        self, limit: int = 10, page: int = 1
    ) -> List[ToDoORM]:
        pass

    @abstractmethod
    async def count_deleted(self) -> int:
        pass

    @abstractmethod
    async def restore_to_do(self, to_do_id: uuid.UUID) -> Optional[ToDoORM]:
        pass


class ToDoRepository(ToDoRepositoryInterface):
    """Repository for ToDos (SQL-injection-safe, async)."""

    def __init__(self, session_manager: Callable, logger: CustomLogger):  # type: ignore[type-arg]
        self.session_manager = session_manager
        self.logger = logger

    async def create_to_do(self, entry: ToDoORM) -> None:
        async with self.session_manager() as session:
            try:
                session.add(entry)
            except IntegrityError as e:
                self.logger.error("Integrity error during insert: %s", e)
                raise

    async def delete_to_do(self, entry_id: uuid.UUID) -> bool:
        entry = await self.get_to_do_entry(entry_id)
        if not entry:
            return False
        async with self.session_manager() as session:
            entry.deleted = True
            entry.updated_at = datetime.datetime.now(datetime.timezone.utc)
            await session.merge(entry)
        return True

    async def hard_delete_to_do(self, to_do_id: uuid.UUID) -> bool:
        async with self.session_manager() as session:
            result = await session.execute(
                select(ToDoORM).where(ToDoORM.id == to_do_id)
            )
            entry = result.scalars().first()
            if not entry:
                return False
            await session.delete(entry)
        return True

    async def update_to_do(
        self, entry_id: uuid.UUID, data: TodoUpdateScheme
    ) -> Optional[ToDoORM]:
        async with self.session_manager() as session:
            result = await session.execute(
                select(ToDoORM).where(
                    ToDoORM.id == entry_id, ToDoORM.deleted.is_(False)
                )
            )
            entry = result.scalars().first()
            if not entry:
                return None
            for key, value in data.model_dump(exclude_unset=True).items():
                setattr(entry, key, value)
            entry.updated_at = datetime.datetime.now(datetime.timezone.utc)
            try:
                await session.merge(entry)
            except IntegrityError as e:
                self.logger.error("Integrity error during update: %s", e)
                raise
            return entry

    async def get_to_do_entry(self, entry_id: uuid.UUID) -> Optional[ToDoORM]:
        async with self.session_manager() as session:
            result = await session.execute(
                select(ToDoORM).where(
                    ToDoORM.id == entry_id, ToDoORM.deleted.is_(False)
                )
            )
            return result.scalars().first()

    async def get_all_to_do_entries(
        self, limit: int = 10, page: int = 1
    ) -> List[ToDoORM]:
        skip = (page - 1) * limit
        async with self.session_manager() as session:
            result = await session.execute(
                select(ToDoORM)
                .where(ToDoORM.deleted.is_(False))
                .offset(skip)
                .limit(limit)
            )
            return list(result.scalars().all())

    async def count_active(self) -> int:
        async with self.session_manager() as session:
            result = await session.execute(
                select(func.count())
                .select_from(ToDoORM)
                .where(ToDoORM.deleted.is_(False))
            )
            return result.scalar_one()

    async def get_deleted_entries(
        self, limit: int = 10, page: int = 1
    ) -> List[ToDoORM]:
        skip = (page - 1) * limit
        async with self.session_manager() as session:
            result = await session.execute(
                select(ToDoORM)
                .where(ToDoORM.deleted.is_(True))
                .offset(skip)
                .limit(limit)
            )
            return list(result.scalars().all())

    async def count_deleted(self) -> int:
        async with self.session_manager() as session:
            result = await session.execute(
                select(func.count())
                .select_from(ToDoORM)
                .where(ToDoORM.deleted.is_(True))
            )
            return result.scalar_one()

    async def restore_to_do(self, to_do_id: uuid.UUID) -> Optional[ToDoORM]:
        async with self.session_manager() as session:
            result = await session.execute(
                select(ToDoORM).where(ToDoORM.id == to_do_id, ToDoORM.deleted.is_(True))
            )
            entry = result.scalars().first()
            if not entry:
                return None
            entry.deleted = False
            entry.updated_at = datetime.datetime.now(datetime.timezone.utc)
            await session.merge(entry)
            return entry
