"""Functional test configuration and fixtures."""

import pytest


@pytest.fixture(scope="function")
def functional_test_data():
    """Provide test data for functional tests."""
    return {
        "test_id": 1,
        "test_name": "functional_test",
    }
