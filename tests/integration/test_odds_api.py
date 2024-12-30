"""Integration tests for the Odds API client."""

import pytest
import requests_mock
from datetime import datetime, timezone

from src.api.odds_api import OddsAPI


@pytest.fixture
def odds_api():
    """Create an OddsAPI instance with test configuration."""
    return OddsAPI(api_key="test_api_key")


def test_get_sports(odds_api, requests_mock):
    """Test getting list of available sports."""
    mock_response = [
        {"key": "basketball_nba", "title": "NBA"},
        {"key": "basketball_ncaab", "title": "NCAAB"},
    ]
    requests_mock.get(
        "https://api.the-odds-api.com/v4/sports?apiKey=test_api_key&regions=us&markets=h2h%2Cspreads%2Ctotals&dateFormat=iso&oddsFormat=american",
        json=mock_response,
    )

    response = odds_api.get_sports()
    assert response == mock_response


def test_get_odds(odds_api, requests_mock):
    """Test getting odds for a sport."""
    mock_response = {"success": True, "data": [{"game": "test", "odds": 1.5}]}
    requests_mock.get(
        "https://api.the-odds-api.com/v4/sports/basketball_nba/odds?apiKey=test_api_key&regions=us&markets=h2h%2Cspreads%2Ctotals&dateFormat=iso&oddsFormat=american",
        json=mock_response,
    )

    response = odds_api.get_odds("basketball_nba")
    assert response == mock_response


def test_get_scores(odds_api, requests_mock):
    """Test getting scores for a sport."""
    mock_response = {"success": True, "data": [{"game": "test", "score": "100-95"}]}
    requests_mock.get(
        "https://api.the-odds-api.com/v4/sports/basketball_nba/scores?apiKey=test_api_key&regions=us&markets=h2h%2Cspreads%2Ctotals&dateFormat=iso&oddsFormat=american&daysFrom=1",
        json=mock_response,
    )

    response = odds_api.get_scores("basketball_nba")
    assert response == mock_response


def test_get_events(odds_api, requests_mock):
    """Test getting events for a sport."""
    mock_response = [
        {
            "id": "19588d18dd485a02f3cd4b0205255548",
            "sport_key": "basketball_nba",
            "sport_title": "NBA",
            "commence_time": "2024-12-28T20:10:00Z",
            "home_team": "Atlanta Hawks",
            "away_team": "Miami Heat",
        }
    ]
    current_time = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    requests_mock.get(
        f"https://api.the-odds-api.com/v4/sports/basketball_nba/events?apiKey=test_api_key&regions=us&markets=h2h%2Cspreads%2Ctotals&dateFormat=iso&oddsFormat=american&commence_time={current_time}",
        json=mock_response,
    )

    response = odds_api.get_events("basketball_nba")
    assert response == mock_response


def test_get_event_odds(odds_api, requests_mock):
    """Test getting odds for a specific event."""
    event_id = "19588d18dd485a02f3cd4b0205255548"
    mock_response = {
        "id": event_id,
        "sport_key": "basketball_nba",
        "sport_title": "NBA",
        "commence_time": "2024-12-28T20:10:00Z",
        "home_team": "Atlanta Hawks",
        "away_team": "Miami Heat",
        "bookmakers": [
            {
                "key": "fanduel",
                "title": "FanDuel",
                "markets": [
                    {
                        "key": "h2h",
                        "outcomes": [
                            {"name": "Atlanta Hawks", "price": -110},
                            {"name": "Miami Heat", "price": -110},
                        ],
                    }
                ],
            }
        ],
    }
    requests_mock.get(
        f"https://api.the-odds-api.com/v4/sports/basketball_nba/events/{event_id}/odds?apiKey=test_api_key&regions=us&markets=h2h%2Cspreads%2Ctotals&dateFormat=iso&oddsFormat=american",
        json=mock_response,
    )

    response = odds_api.get_event_odds("basketball_nba", event_id)
    assert response == mock_response


def test_api_error_handling(odds_api, requests_mock):
    """Test handling of various API errors."""
    # Test 404 error
    requests_mock.get(
        "https://api.the-odds-api.com/v4/sports?apiKey=test_api_key&regions=us&markets=h2h%2Cspreads%2Ctotals&dateFormat=iso&oddsFormat=american",
        status_code=404,
    )
    response = odds_api.get_sports()
    assert response is None

    # Test rate limit error
    requests_mock.get(
        "https://api.the-odds-api.com/v4/sports?apiKey=test_api_key&regions=us&markets=h2h%2Cspreads%2Ctotals&dateFormat=iso&oddsFormat=american",
        status_code=429,
    )
    response = odds_api.get_sports()
    assert response is None

    # Test server error
    requests_mock.get(
        "https://api.the-odds-api.com/v4/sports?apiKey=test_api_key&regions=us&markets=h2h%2Cspreads%2Ctotals&dateFormat=iso&oddsFormat=american",
        status_code=500,
    )
    response = odds_api.get_sports()
    assert response is None


def test_invalid_parameters(odds_api, requests_mock):
    """Test handling of invalid parameters."""
    # Test invalid sport
    requests_mock.get(
        "https://api.the-odds-api.com/v4/sports/invalid/odds?apiKey=test_api_key&regions=us&markets=h2h%2Cspreads%2Ctotals&dateFormat=iso&oddsFormat=american",
        status_code=401,
    )
    response = odds_api.get_odds("invalid")
    assert response is None

    # Test invalid sport for scores
    requests_mock.get(
        "https://api.the-odds-api.com/v4/sports/invalid/scores?apiKey=test_api_key&regions=us&markets=h2h%2Cspreads%2Ctotals&dateFormat=iso&oddsFormat=american&daysFrom=1",
        status_code=401,
    )
    response = odds_api.get_scores("invalid")
    assert response is None

    # Test invalid sport for events
    current_time = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    requests_mock.get(
        f"https://api.the-odds-api.com/v4/sports/invalid/events?apiKey=test_api_key&regions=us&markets=h2h%2Cspreads%2Ctotals&dateFormat=iso&oddsFormat=american&commence_time={current_time}",
        status_code=401,
    )
    response = odds_api.get_events("invalid")
    assert response is None

    # Test invalid event ID
    requests_mock.get(
        "https://api.the-odds-api.com/v4/sports/basketball_nba/events/invalid/odds?apiKey=test_api_key&regions=us&markets=h2h%2Cspreads%2Ctotals&dateFormat=iso&oddsFormat=american",
        status_code=401,
    )
    response = odds_api.get_event_odds("basketball_nba", "invalid")
    assert response is None
