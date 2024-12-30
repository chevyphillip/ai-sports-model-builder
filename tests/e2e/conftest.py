"""End-to-end test configuration and fixtures."""

import pytest


@pytest.fixture(scope="function")
def e2e_test_data():
    """Provide test data for end-to-end tests."""
    return {
        "test_id": 1,
        "test_name": "e2e_test",
    }
