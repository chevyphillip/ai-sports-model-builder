"""Tests for the OddsAPI client."""

import os
import pytest
from datetime import datetime, timezone
from src.data_collection.odds_api_client import OddsAPIClient


def test_get_start_of_day_timestamp():
    """Test the _get_start_of_day_timestamp helper method."""
    client = OddsAPIClient()

    # Test with specific date
    test_date = "2024-12-01T15:30:45Z"
    expected = "2024-12-01T00:00:00Z"
    assert client._get_start_of_day_timestamp(test_date) == expected

    # Test with invalid date format
    invalid_date = "2024-12-01"  # Missing time component
    result = client._get_start_of_day_timestamp(invalid_date)
    assert result.endswith("T00:00:00Z")

    # Test without date (should use current date)
    result = client._get_start_of_day_timestamp()
    today = datetime.now(timezone.utc).date()
    expected_today = datetime.combine(today, datetime.min.time()).replace(
        tzinfo=timezone.utc
    )
    assert result == expected_today.isoformat().replace("+00:00", "Z")


def test_get_historical_odds():
    """Test fetching historical odds data."""
    client = OddsAPIClient()

    # Test with specific date
    test_date = "2024-12-01T00:00:00Z"
    data, error = client.get_historical_odds(date=test_date)

    if error:
        print(f"API Error: {error}")
    else:
        assert isinstance(data, dict)
        assert "timestamp" in data
        assert "data" in data

        # Verify the response structure
        if data.get("data"):
            game = data["data"][0]
            assert "id" in game
            assert "sport_key" in game
            assert "sport_title" in game
            assert "commence_time" in game
            assert "home_team" in game
            assert "away_team" in game
            assert "bookmakers" in game

            # Verify bookmaker data structure
            if game["bookmakers"]:
                bookmaker = game["bookmakers"][0]
                assert "key" in bookmaker
                assert "title" in bookmaker
                assert "markets" in bookmaker

                # Verify markets structure
                if bookmaker["markets"]:
                    market = bookmaker["markets"][0]
                    assert "key" in market
                    assert "outcomes" in market


def test_error_handling():
    """Test error handling with invalid API key."""
    client = OddsAPIClient(api_key="invalid_key")
    data, error = client.get_historical_odds()

    assert not data  # Should be empty dict
    assert error is not None  # Should have error message
    assert (
        "401" in error or "unauthorized" in error.lower()
    )  # Should indicate auth error
