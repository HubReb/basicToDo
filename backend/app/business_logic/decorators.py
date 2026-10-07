"""Decorators for business logic layer."""

import functools
import inspect
from typing import Any, Callable, TypeVar, cast

from sqlalchemy.exc import IntegrityError

from backend.app.business_logic.exceptions import (
    ToDoAlreadyExistsError,
    ToDoNotFoundError,
    ToDoRepositoryError,
    ToDoValidationError,
)

_F = TypeVar("_F", bound=Callable[..., Any])


def is_duplicate_id(exc: IntegrityError) -> bool:
    """Q6.3: a primary-key clash, as opposed to a CHECK or NOT NULL violation."""
    orig = exc.orig
    return getattr(
        orig, "sqlite_errorname", None
    ) == "SQLITE_CONSTRAINT_PRIMARYKEY" or "UNIQUE constraint failed: toDo.id" in str(
        orig
    )


def handle_service_exceptions(func: _F) -> _F:
    """Decorator to handle common service layer exceptions with unified logging."""

    @functools.wraps(func)
    async def async_wrapper(self: Any, *args: Any, **kwargs: Any) -> Any:
        try:
            return await func(self, *args, **kwargs)
        except ToDoValidationError as ve:
            self.logger.warning("Validation error: %s", ve)
            raise
        except ToDoNotFoundError:
            self.logger.error("ToDo not found")
            raise
        except IntegrityError as exc:
            if is_duplicate_id(exc):
                raise ToDoAlreadyExistsError from None
            self.logger.error("Integrity error in %s: %s", func.__name__, exc)
            raise ToDoRepositoryError from exc
        except Exception as exc:
            self.logger.error("Error in %s: %s", func.__name__, exc)
            raise ToDoRepositoryError from exc

    @functools.wraps(func)
    def sync_wrapper(self: Any, *args: Any, **kwargs: Any) -> Any:
        try:
            return func(self, *args, **kwargs)
        except ToDoValidationError as ve:
            self.logger.warning("Validation error: %s", ve)
            raise
        except ToDoNotFoundError:
            self.logger.error("ToDo not found")
            raise
        except IntegrityError as exc:
            if is_duplicate_id(exc):
                raise ToDoAlreadyExistsError from None
            self.logger.error("Integrity error in %s: %s", func.__name__, exc)
            raise ToDoRepositoryError from exc
        except Exception as exc:
            self.logger.error("Error in %s: %s", func.__name__, exc)
            raise ToDoRepositoryError from exc

    return cast(
        _F, async_wrapper if inspect.iscoroutinefunction(func) else sync_wrapper
    )
