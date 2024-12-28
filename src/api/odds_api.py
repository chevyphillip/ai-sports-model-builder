"""Client for interacting with The Odds API."""

import logging
import urllib.parse
from typing import Any, Dict, List, Optional

import requests

logger = logging.getLogger(__name__)


class OddsAPI:
    """Client for The Odds API."""

    def __init__(self, api_key: str):
        """Initialize the client.

        Args:
            api_key: The API key for The Odds API.
        """
        self.api_key = api_key
        self.base_url = "https://api.the-odds-api.com/v4"

    def _make_request(
        self, endpoint: str, params: Optional[Dict[str, Any]] = None
    ) -> Any:
        """Make a request to The Odds API.

        Args:
            endpoint: The API endpoint to call.
            params: Optional query parameters.

        Returns:
            The response data or an empty list if the request fails.
        """
        if params is None:
            params = {}

        # Add API key to query parameters
        params["apiKey"] = self.api_key

        # Format the endpoint with sport parameter if needed
        if "{sport}" in endpoint:
            sport = params.pop("sport", "")
            # URL encode the sport key
            sport = urllib.parse.quote(sport, safe="")
            endpoint = endpoint.format(sport=sport)

        url = f"{self.base_url}/{endpoint}"
        try:
            response = requests.get(url, params=params)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Error making request to Odds API: {e}")
            return []

    def get_sports(self) -> List[Dict[str, Any]]:
        """Get a list of available sports.

        Returns:
            A list of sports data or an empty list if the request fails.
        """
        return self._make_request("sports")

    def get_odds(self, sport: str) -> List[Dict[str, Any]]:
        """Get odds for a specific sport.

        Args:
            sport: The sport key (e.g., "basketball_nba").

        Returns:
            A list of odds data or an empty list if the request fails.
        """
        params = {
            "sport": sport,
            "regions": "us",
            "markets": "h2h,spreads,totals",
        }
        return self._make_request("sports/{sport}/odds", params)

    def get_scores(self, sport: str, days_from: int = 1) -> List[Dict[str, Any]]:
        """Get scores for a specific sport.

        Args:
            sport: The sport key (e.g., "basketball_nba").
            days_from: Number of days from today to include (-1 for yesterday).

        Returns:
            A list of scores data or an empty list if the request fails.
        """
        params = {
            "sport": sport,
            "daysFrom": days_from,
        }
        return self._make_request("sports/{sport}/scores", params)

    def get_events(self, sport: str) -> List[Dict[str, Any]]:
        """Get events for a specific sport.

        Args:
            sport: The sport key (e.g., "basketball_nba").

        Returns:
            A list of events data or an empty list if the request fails.
        """
        params = {"sport": sport}
        return self._make_request("sports/{sport}/events", params)

    def get_event_odds(
        self,
        sport: str,
        event_id: str,
        regions: str = "us",
        markets: str = "h2h,spreads,totals",
        date_format: str = "iso",
        odds_format: str = "decimal",
    ) -> List[Dict[str, Any]]:
        """Get odds for a specific event.

        Args:
            sport: The sport key (e.g., "basketball_nba").
            event_id: The event ID.
            regions: Comma-separated list of regions (default: "us").
            markets: Comma-separated list of markets (default: "h2h,spreads,totals").
            date_format: Date format (default: "iso").
            odds_format: Odds format (default: "decimal").

        Returns:
            A list of event odds data or an empty list if the request fails.
        """
        params = {
            "sport": sport,
            "regions": regions,
            "markets": markets,
            "dateFormat": date_format,
            "oddsFormat": odds_format,
        }
        return self._make_request(f"sports/{{sport}}/events/{event_id}/odds", params)


# Usage example:
if __name__ == "__main__":
    client = OddsAPI("your_api_key")
    sports = client.get_sports()
    if sports:
        logger.info(f"Available sports: {sports}")
