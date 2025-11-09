"""Decorators for business logic layer."""
import asyncio
import functools
from typing import Any, Callable, TypeVar, cast

from sqlalchemy.exc import IntegrityError

from backend.app.business_logic.exceptions import (
    ToDoAlreadyExistsError,
    ToDoNotFoundError,
    ToDoRepositoryError,
    ToDoValidationError,
)

_F = TypeVar('_F', bound=Callable[..., Any])


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
        except IntegrityError:
            raise ToDoAlreadyExistsError from None
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
        except IntegrityError:
            raise ToDoAlreadyExistsError from None
        except Exception as exc:
            self.logger.error("Error in %s: %s", func.__name__, exc)
            raise ToDoRepositoryError from exc

    return cast(_F, async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper)