"""Shared fixtures for ToDoService integration tests.

This conftest imports shared fixtures from the root conftest and provides
a service fixture alias for backward compatibility.
"""
import pytest


@pytest.fixture
def todo_service(todo_service_integration):
    """Alias for the integration service fixture from root conftest.

    This maintains backward compatibility with existing integration tests.
    """
    return todo_service_integration
