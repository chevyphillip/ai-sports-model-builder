"""Edge case tests for the Odds API client."""

import json
from datetime import datetime, timedelta

import pytest
import requests
import requests_mock

from src.api.odds_api import OddsAPI


@pytest.fixture
def odds_api_client():
    """Create an Odds API client for testing."""
    return OddsAPI(api_key="test_api_key")


def test_empty_response(odds_api_client, requests_mock):
    """Test handling of empty response data."""
    requests_mock.get(
        "https://api.the-odds-api.com/v4/sports",
        json=[],
    )
    result = odds_api_client.get_sports()
    assert result == []


def test_malformed_json_response(odds_api_client, requests_mock):
    """Test handling of malformed JSON response."""
    requests_mock.get(
        "https://api.the-odds-api.com/v4/sports",
        text="invalid json",
    )
    result = odds_api_client.get_sports()
    assert result == []


def test_connection_timeout(odds_api_client, requests_mock):
    """Test handling of connection timeout."""
    requests_mock.get(
        "https://api.the-odds-api.com/v4/sports",
        exc=requests.exceptions.ConnectTimeout,
    )
    result = odds_api_client.get_sports()
    assert result == []


def test_connection_error(odds_api_client, requests_mock):
    """Test handling of connection error."""
    requests_mock.get(
        "https://api.the-odds-api.com/v4/sports",
        exc=requests.exceptions.ConnectionError,
    )
    result = odds_api_client.get_sports()
    assert result == []


def test_null_values_in_response(odds_api_client, requests_mock):
    """Test handling of null values in response."""
    mock_response = [
        {
            "key": "basketball_nba",
            "group": None,
            "title": "NBA",
            "description": None,
            "active": True,
            "has_outrights": None,
        }
    ]
    requests_mock.get(
        "https://api.the-odds-api.com/v4/sports",
        json=mock_response,
    )
    result = odds_api_client.get_sports()
    assert result == mock_response


def test_empty_sport_key(odds_api_client, requests_mock):
    """Test handling of empty sport key."""
    requests_mock.get(
        "https://api.the-odds-api.com/v4/sports//odds",
        status_code=404,
    )
    result = odds_api_client.get_odds("")
    assert result == []


def test_special_characters_in_sport_key(odds_api_client, requests_mock):
    """Test handling of special characters in sport key."""
    requests_mock.get(
        "https://api.the-odds-api.com/v4/sports/test%21%40%23/odds",
        status_code=404,
    )
    result = odds_api_client.get_odds("test!@#")
    assert result == []


def test_future_dates_in_scores(odds_api_client, requests_mock):
    """Test handling of future dates in scores endpoint."""
    future_date = (datetime.utcnow() + timedelta(days=7)).strftime("%Y-%m-%d")
    requests_mock.get(
        "https://api.the-odds-api.com/v4/sports/basketball_nba/scores",
        json=[],
    )
    result = odds_api_client.get_scores("basketball_nba", days_from=7)
    assert result == []


def test_large_response(odds_api_client, requests_mock):
    """Test handling of large response data."""
    # Create a large response with 1000 events
    large_response = []
    for i in range(1000):
        large_response.append(
            {
                "id": str(i),
                "sport_key": "basketball_nba",
                "sport_title": "NBA",
                "commence_time": "2024-01-01T00:00:00Z",
                "completed": True,
                "home_team": f"Team {i} Home",
                "away_team": f"Team {i} Away",
                "scores": [
                    {"name": f"Team {i} Home", "score": 100},
                    {"name": f"Team {i} Away", "score": 95},
                ],
            }
        )

    requests_mock.get(
        "https://api.the-odds-api.com/v4/sports/basketball_nba/scores",
        json=large_response,
    )
    result = odds_api_client.get_scores("basketball_nba")
    assert result == large_response
    assert len(result) == 1000


def test_unicode_team_names(odds_api_client, requests_mock):
    """Test handling of Unicode characters in team names."""
    mock_response = [
        {
            "id": "1",
            "sport_key": "soccer_spain_la_liga",
            "sport_title": "La Liga",
            "commence_time": "2024-01-01T00:00:00Z",
            "home_team": "Atlético Madrid",  # Unicode character
            "away_team": "Real Betis Balompié",  # Unicode character
            "bookmakers": [
                {
                    "key": "betfair",
                    "title": "Betfair",
                    "markets": [
                        {
                            "key": "h2h",
                            "outcomes": [
                                {"name": "Atlético Madrid", "price": 1.91},
                                {"name": "Real Betis Balompié", "price": 1.91},
                            ],
                        }
                    ],
                }
            ],
        }
    ]
    requests_mock.get(
        "https://api.the-odds-api.com/v4/sports/soccer_spain_la_liga/odds",
        json=mock_response,
    )
    result = odds_api_client.get_odds("soccer_spain_la_liga")
    assert result == mock_response


def test_invalid_date_format(odds_api_client, requests_mock):
    """Test handling of invalid date format parameter."""
    requests_mock.get(
        "https://api.the-odds-api.com/v4/sports/basketball_nba/events/1/odds",
        status_code=400,
    )
    result = odds_api_client.get_event_odds(
        "basketball_nba", "1", date_format="invalid"
    )
    assert result == []


def test_invalid_odds_format(odds_api_client, requests_mock):
    """Test handling of invalid odds format parameter."""
    requests_mock.get(
        "https://api.the-odds-api.com/v4/sports/basketball_nba/events/1/odds",
        status_code=400,
    )
    result = odds_api_client.get_event_odds(
        "basketball_nba", "1", odds_format="invalid"
    )
    assert result == []


def test_missing_required_fields(odds_api_client, requests_mock):
    """Test handling of missing required fields in response."""
    mock_response = [
        {
            # Missing id
            "sport_key": "basketball_nba",
            # Missing sport_title
            "commence_time": "2024-01-01T00:00:00Z",
            # Missing home_team
            "away_team": "Golden State Warriors",
            "bookmakers": [],  # Empty bookmakers
        }
    ]
    requests_mock.get(
        "https://api.the-odds-api.com/v4/sports/basketball_nba/odds",
        json=mock_response,
    )
    result = odds_api_client.get_odds("basketball_nba")
    assert result == mock_response  # Client should return data as-is


def test_rate_limit_headers(odds_api_client, requests_mock):
    """Test handling of rate limit headers."""
    headers = {
        "X-Requests-Remaining": "10",
        "X-Requests-Used": "90",
    }
    requests_mock.get(
        "https://api.the-odds-api.com/v4/sports",
        json=[],
        headers=headers,
    )
    result = odds_api_client.get_sports()
    assert result == []  # Client should ignore headers
