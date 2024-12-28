"""Integration test configuration and fixtures."""

import pytest


@pytest.fixture(scope="function")
def integration_test_data():
    """Provide test data for integration tests."""
    return {
        "test_id": 1,
        "test_name": "integration_test",
    }
