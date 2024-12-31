"""Basic smoke tests to verify test setup."""

import pytest


@pytest.mark.smoke
def test_pytest_setup():
    """Verify that pytest is properly configured."""
    assert True


@pytest.mark.smoke
def test_pytest_fixture_setup(tmp_path):
    """Verify that pytest fixtures are working."""
    test_file = tmp_path / "test.txt"
    test_file.write_text("Test content")
    assert test_file.read_text() == "Test content"


@pytest.mark.smoke
def test_pytest_raises():
    """Verify that pytest exception handling is working."""
    with pytest.raises(ValueError):
        raise ValueError("Test exception")
