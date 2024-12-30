"""Basic unit tests."""

import pytest


@pytest.mark.unit
def test_unit_fixture(unit_test_data):
    """Test that unit test fixtures are working."""
    assert unit_test_data["test_id"] == 1
    assert unit_test_data["test_name"] == "unit_test"
