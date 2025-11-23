"""Shared fixtures for ToDoService unit tests.

This conftest imports shared fixtures from the root conftest and provides
a service fixture alias for backward compatibility.
"""
import pytest


@pytest.fixture
def todo_service(todo_service_with_mock_repo):
    """Alias for the standard service fixture from root conftest.

    This maintains backward compatibility with existing unit tests.
    """
    return todo_service_with_mock_repo
