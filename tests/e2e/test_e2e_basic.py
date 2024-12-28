"""Basic end-to-end tests."""

import pytest


@pytest.mark.e2e
def test_e2e_fixture(e2e_test_data):
    """Test that end-to-end test fixtures are working."""
    assert e2e_test_data["test_id"] == 1
    assert e2e_test_data["test_name"] == "e2e_test"
