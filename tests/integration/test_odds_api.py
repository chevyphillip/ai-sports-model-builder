"""Integration tests for the Odds API client."""

import pytest
import requests_mock

from src.api.odds_api import OddsAPI


@pytest.fixture
def odds_api_client():
    """Create an Odds API client for testing."""
    return OddsAPI(api_key="test_api_key")


@pytest.fixture
def mock_sports_response():
    """Mock response for the sports endpoint."""
    return [
        {
            "key": "basketball_nba",
            "group": "Basketball",
            "title": "NBA",
            "description": "US Basketball",
            "active": True,
            "has_outrights": False,
        }
    ]


@pytest.fixture
def mock_odds_response():
    """Mock response for the odds endpoint."""
    return [
        {
            "id": "1",
            "sport_key": "basketball_nba",
            "sport_title": "NBA",
            "commence_time": "2024-01-01T00:00:00Z",
            "home_team": "Los Angeles Lakers",
            "away_team": "Golden State Warriors",
            "bookmakers": [
                {
                    "key": "fanduel",
                    "title": "FanDuel",
                    "markets": [
                        {
                            "key": "h2h",
                            "outcomes": [
                                {"name": "Los Angeles Lakers", "price": 1.91},
                                {"name": "Golden State Warriors", "price": 1.91},
                            ],
                        }
                    ],
                }
            ],
        }
    ]


@pytest.fixture
def mock_scores_response():
    """Mock response for the scores endpoint."""
    return [
        {
            "id": "1",
            "sport_key": "basketball_nba",
            "sport_title": "NBA",
            "commence_time": "2024-01-01T00:00:00Z",
            "completed": True,
            "home_team": "Los Angeles Lakers",
            "away_team": "Golden State Warriors",
            "scores": [
                {"name": "Los Angeles Lakers", "score": 120},
                {"name": "Golden State Warriors", "score": 110},
            ],
            "last_update": "2024-01-01T02:30:00Z",
        }
    ]


@pytest.fixture
def mock_events_response():
    """Mock response for the events endpoint."""
    return [
        {
            "id": "1",
            "sport_key": "basketball_nba",
            "sport_title": "NBA",
            "commence_time": "2024-01-01T00:00:00Z",
            "home_team": "Los Angeles Lakers",
            "away_team": "Golden State Warriors",
            "status": "upcoming",
        }
    ]


@pytest.fixture
def mock_event_odds_response():
    """Mock response for the event odds endpoint."""
    return [
        {
            "id": "1",
            "sport_key": "basketball_nba",
            "sport_title": "NBA",
            "commence_time": "2024-01-01T00:00:00Z",
            "home_team": "Los Angeles Lakers",
            "away_team": "Golden State Warriors",
            "bookmakers": [
                {
                    "key": "fanduel",
                    "title": "FanDuel",
                    "markets": [
                        {
                            "key": "h2h",
                            "outcomes": [
                                {"name": "Los Angeles Lakers", "price": 1.91},
                                {"name": "Golden State Warriors", "price": 1.91},
                            ],
                        }
                    ],
                }
            ],
        }
    ]


def test_get_sports(odds_api_client, mock_sports_response, requests_mock):
    """Test getting sports data."""
    requests_mock.get(
        "https://api.the-odds-api.com/v4/sports",
        json=mock_sports_response,
    )

    result = odds_api_client.get_sports()
    assert result == mock_sports_response
    assert len(result) == 1
    assert result[0]["key"] == "basketball_nba"


def test_get_odds(odds_api_client, mock_odds_response, requests_mock):
    """Test getting odds data."""
    requests_mock.get(
        "https://api.the-odds-api.com/v4/sports/basketball_nba/odds",
        json=mock_odds_response,
    )

    result = odds_api_client.get_odds("basketball_nba")
    assert result == mock_odds_response
    assert len(result) == 1
    assert result[0]["sport_key"] == "basketball_nba"


def test_get_scores(odds_api_client, mock_scores_response, requests_mock):
    """Test getting scores data."""
    requests_mock.get(
        "https://api.the-odds-api.com/v4/sports/basketball_nba/scores",
        json=mock_scores_response,
    )

    result = odds_api_client.get_scores("basketball_nba")
    assert result == mock_scores_response
    assert len(result) == 1
    assert result[0]["sport_key"] == "basketball_nba"


def test_get_events(odds_api_client, mock_events_response, requests_mock):
    """Test getting events data."""
    requests_mock.get(
        "https://api.the-odds-api.com/v4/sports/basketball_nba/events",
        json=mock_events_response,
    )

    result = odds_api_client.get_events("basketball_nba")
    assert result == mock_events_response
    assert len(result) == 1
    assert result[0]["sport_key"] == "basketball_nba"


def test_get_event_odds(odds_api_client, mock_event_odds_response, requests_mock):
    """Test getting event odds data."""
    requests_mock.get(
        "https://api.the-odds-api.com/v4/sports/basketball_nba/events/1/odds",
        json=mock_event_odds_response,
    )

    result = odds_api_client.get_event_odds("basketball_nba", "1")
    assert result == mock_event_odds_response
    assert len(result) == 1
    assert result[0]["sport_key"] == "basketball_nba"


def test_api_error_handling(odds_api_client, requests_mock):
    """Test handling of API errors."""
    # Test 404 error
    requests_mock.get(
        "https://api.the-odds-api.com/v4/sports",
        status_code=404,
    )
    result = odds_api_client.get_sports()
    assert result == []

    # Test 429 error (rate limit)
    requests_mock.get(
        "https://api.the-odds-api.com/v4/sports",
        status_code=429,
    )
    result = odds_api_client.get_sports()
    assert result == []

    # Test 500 error
    requests_mock.get(
        "https://api.the-odds-api.com/v4/sports",
        status_code=500,
    )
    result = odds_api_client.get_sports()
    assert result == []


def test_invalid_parameters(odds_api_client, requests_mock):
    """Test handling of invalid parameters."""
    # Test invalid sport key for odds
    requests_mock.get(
        "https://api.the-odds-api.com/v4/sports/invalid/odds",
        status_code=401,
    )
    result = odds_api_client.get_odds("invalid")
    assert result == []

    # Test invalid sport key for scores
    requests_mock.get(
        "https://api.the-odds-api.com/v4/sports/invalid/scores",
        status_code=401,
    )
    result = odds_api_client.get_scores("invalid")
    assert result == []

    # Test invalid sport key for events
    requests_mock.get(
        "https://api.the-odds-api.com/v4/sports/invalid/events",
        status_code=401,
    )
    result = odds_api_client.get_events("invalid")
    assert result == []

    # Test invalid event ID for event odds
    requests_mock.get(
        "https://api.the-odds-api.com/v4/sports/basketball_nba/events/invalid/odds",
        status_code=401,
    )
    result = odds_api_client.get_event_odds("basketball_nba", "invalid")
    assert result == []
