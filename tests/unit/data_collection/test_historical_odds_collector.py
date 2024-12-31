"""Tests for the historical odds collector."""

import pytest
from datetime import datetime, timezone
import json
from pathlib import Path
import tempfile
import shutil
from src.data_collection.historical_odds_collector import HistoricalOddsCollector


@pytest.fixture
def temp_output_dir():
    """Create a temporary directory for test outputs."""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir)


@pytest.fixture
def sample_odds_data():
    """Sample odds data for testing."""
    return [
        {
            "timestamp": "2024-01-01T00:00:00Z",
            "previous_timestamp": "2023-12-31T23:55:00Z",
            "next_timestamp": "2024-01-01T00:05:00Z",
            "data": [
                {
                    "id": "test_game_1",
                    "sport_key": "basketball_nba",
                    "sport_title": "NBA",
                    "commence_time": "2024-01-01T00:00:00Z",
                    "home_team": "Los Angeles Lakers",
                    "away_team": "Golden State Warriors",
                    "bookmakers": [
                        {
                            "key": "draftkings",
                            "title": "DraftKings",
                            "last_update": "2024-01-01T00:00:00Z",
                            "markets": [
                                {
                                    "key": "h2h",
                                    "last_update": "2024-01-01T00:00:00Z",
                                    "outcomes": [
                                        {"name": "Los Angeles Lakers", "price": -110},
                                        {
                                            "name": "Golden State Warriors",
                                            "price": -110,
                                        },
                                    ],
                                },
                                {
                                    "key": "spreads",
                                    "last_update": "2024-01-01T00:00:00Z",
                                    "outcomes": [
                                        {
                                            "name": "Los Angeles Lakers",
                                            "price": -110,
                                            "point": -2.5,
                                        },
                                        {
                                            "name": "Golden State Warriors",
                                            "price": -110,
                                            "point": 2.5,
                                        },
                                    ],
                                },
                            ],
                        }
                    ],
                }
            ],
        }
    ]


def test_generate_date_range():
    """Test date range generation."""
    collector = HistoricalOddsCollector()
    dates = collector._generate_date_range(2024, 2024)

    assert len(dates) == 366  # 2024 is a leap year
    assert dates[0] == "2024-01-01T00:00:00Z"
    assert dates[-1] == "2024-12-31T00:00:00Z"

    # Test date format
    for date in dates:
        # Verify ISO8601 format
        try:
            datetime.fromisoformat(date.replace("Z", "+00:00"))
        except ValueError:
            pytest.fail(f"Invalid date format: {date}")


def test_analyze_data_structure(sample_odds_data):
    """Test data structure analysis."""
    collector = HistoricalOddsCollector()
    analysis = collector.analyze_data_structure(sample_odds_data)

    assert analysis["total_snapshots"] == 1
    assert analysis["total_games"] == 1
    assert analysis["bookmakers"] == ["draftkings"]
    assert sorted(analysis["market_types"]) == ["h2h", "spreads"]
    assert analysis["date_range"]["start"] == "2024-01-01T00:00:00Z"
    assert analysis["date_range"]["end"] == "2024-01-01T00:00:00Z"

    # Verify sample game structure
    sample_game = analysis["sample_game"]
    assert sample_game["sport_key"] == "basketball_nba"
    assert "home_team" in sample_game
    assert "away_team" in sample_game
    assert "bookmakers" in sample_game

    # Verify bookmaker structure
    bookmaker = sample_game["bookmakers"][0]
    assert "key" in bookmaker
    assert "markets" in bookmaker

    # Verify market structure
    market = bookmaker["markets"][0]
    assert "key" in market
    assert "outcomes" in market

    # Verify outcome structure
    outcome = market["outcomes"][0]
    assert "name" in outcome
    assert "price" in outcome


def test_file_output(temp_output_dir, sample_odds_data):
    """Test file output functionality."""
    collector = HistoricalOddsCollector(output_dir=temp_output_dir)

    # Mock the API call by monkey patching
    def mock_get_historical_odds(*args, **kwargs):
        return sample_odds_data[0], None

    collector.client.get_historical_odds = mock_get_historical_odds

    # Collect data for a single day
    collector.collect_historical_odds(start_year=2024, end_year=2024)

    # Check if file was created
    expected_file = Path(temp_output_dir) / "odds_2024-01-01.json"
    assert expected_file.exists()

    # Verify file contents
    with open(expected_file) as f:
        saved_data = json.load(f)

    assert saved_data == sample_odds_data[0]


def test_error_handling(temp_output_dir):
    """Test error handling during data collection."""
    collector = HistoricalOddsCollector(output_dir=temp_output_dir)

    # Mock API error
    def mock_get_historical_odds(*args, **kwargs):
        return {}, "API Error: Test error"

    collector.client.get_historical_odds = mock_get_historical_odds

    # Collect data for a single day
    collector.collect_historical_odds(start_year=2024, end_year=2024)

    # Check if error file was created
    error_file = Path(temp_output_dir) / "collection_errors.json"
    assert error_file.exists()

    # Verify error contents
    with open(error_file) as f:
        errors = json.load(f)

    assert len(errors) > 0
    assert "date" in errors[0]
    assert "error" in errors[0]
    assert errors[0]["error"] == "API Error: Test error"
