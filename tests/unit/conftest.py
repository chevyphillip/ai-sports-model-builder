"""Unit test configuration and fixtures."""

import pytest


@pytest.fixture(scope="function")
def unit_test_data():
    """Provide test data for unit tests."""
    return {
        "test_id": 1,
        "test_name": "unit_test",
    }
