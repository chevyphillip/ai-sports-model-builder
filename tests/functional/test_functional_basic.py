"""Basic functional tests."""

import pytest


@pytest.mark.functional
def test_functional_fixture(functional_test_data):
    """Test that functional test fixtures are working."""
    assert functional_test_data["test_id"] == 1
    assert functional_test_data["test_name"] == "functional_test"
