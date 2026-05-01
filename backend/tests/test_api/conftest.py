"""API test configuration - disables rate limiting during tests."""
import pytest

from backend.app.api.api import limiter

# Disable rate limiting for all API tests
limiter.enabled = False
