"""Factory classes for creating test data using factory_boy."""
import datetime
import uuid
from typing import Any

import factory
from factory import Factory, Faker, LazyFunction

from backend.app.models.todo import ToDoEntryData
from backend.app.schemas.data_schemes.create_todo_schema import ToDoCreateScheme
from backend.app.schemas.data_schemes.todo_schema import ToDoSchema
from backend.app.schemas.data_schemes.update_todo_schema import TodoUpdateScheme


class ToDoEntryDataFactory(Factory):
    """Factory for creating ToDoEntryData instances."""

    class Meta:  # type: ignore
        model = ToDoEntryData

    id = LazyFunction(uuid.uuid4)
    title = Faker("sentence", nb_words=3)
    description = Faker("sentence", nb_words=6)
    created_at = LazyFunction(datetime.datetime.now)
    updated_at = None
    done = False
    deleted = False


class ToDoCreateSchemeFactory(Factory):
    """Factory for creating ToDoCreateScheme instances."""

    class Meta:  # type: ignore
        model = ToDoCreateScheme

    id = LazyFunction(uuid.uuid4)
    title = Faker("sentence", nb_words=3)
    description = Faker("sentence", nb_words=6)


class TodoUpdateSchemeFactory(Factory):
    """Factory for creating TodoUpdateScheme instances."""

    class Meta:  # type: ignore
        model = TodoUpdateScheme

    id = LazyFunction(uuid.uuid4)
    title = Faker("sentence", nb_words=3)
    description = Faker("sentence", nb_words=6)
    done = False


class ToDoSchemaFactory(Factory):
    """Factory for creating ToDoSchema instances."""

    class Meta:  # type: ignore
        model = ToDoSchema

    id = LazyFunction(uuid.uuid4)
    title = Faker("sentence", nb_words=3)
    description = Faker("sentence", nb_words=6)
    created_at = LazyFunction(datetime.datetime.now)
    updated_at = None
    done = False
    deleted = False


# Convenience functions for common test data patterns
def create_todo_entry(**kwargs: Any) -> ToDoEntryData:
    """Create a ToDoEntryData instance with optional overrides."""
    return ToDoEntryDataFactory.build(**kwargs)


def create_todo_create_scheme(**kwargs: Any) -> ToDoCreateScheme:
    """Create a ToDoCreateScheme instance with optional overrides."""
    return ToDoCreateSchemeFactory.build(**kwargs)


def create_todo_update_scheme(**kwargs: Any) -> TodoUpdateScheme:
    """Create a TodoUpdateScheme instance with optional overrides."""
    return TodoUpdateSchemeFactory.build(**kwargs)


def create_todo_schema(**kwargs: Any) -> ToDoSchema:
    """Create a ToDoSchema instance with optional overrides."""
    return ToDoSchemaFactory.build(**kwargs)
