"""Basic integration tests."""

import pytest


@pytest.mark.integration
def test_integration_fixture(integration_test_data):
    """Test that integration test fixtures are working."""
    assert integration_test_data["test_id"] == 1
    assert integration_test_data["test_name"] == "integration_test"
