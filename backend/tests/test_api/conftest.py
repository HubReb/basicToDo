"""API test fixtures, shared by the modules of this directory."""

# Registered here, so the test modules use them without importing them.
from backend.tests.test_api.test_setup_for_api_endpoins import (  # noqa: F401
    client,
    created_todo,
    mock_service,
)
