"""Client for The Odds API."""

import logging
from datetime import datetime, timezone
import requests
from typing import Optional, Dict, List, Any, Union

logger = logging.getLogger(__name__)


class OddsAPI:
    """Client for The Odds API."""

    def __init__(self, api_key: str):
        """Initialize the API client.

        Args:
            api_key: The API key for authentication
        """
        self.api_key = api_key
        self.base_url = "https://api.the-odds-api.com/v4"
        self.default_params = {
            "apiKey": self.api_key,
            "regions": "us",
            "markets": "h2h,spreads,totals",
            "dateFormat": "iso",
            "oddsFormat": "american",
        }

    def _make_request(
        self, endpoint: str, params: Optional[Dict] = None
    ) -> Optional[Union[Dict, List]]:
        """Make a request to the API.

        Args:
            endpoint: The API endpoint to call
            params: Optional query parameters

        Returns:
            The JSON response or None if the request failed
        """
        url = f"{self.base_url}/{endpoint}"
        request_params = {**self.default_params, **(params or {})}

        try:
            response = requests.get(url, params=request_params)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Error making request to Odds API: {e}")
            return None

    def get_sports(self) -> Optional[List[Dict]]:
        """Get a list of available sports."""
        return self._make_request("sports")

    def get_odds(self, sport: str) -> Optional[List[Dict]]:
        """Get odds for a sport.

        Args:
            sport: The sport key (e.g., 'basketball_nba')
        """
        return self._make_request(f"sports/{sport}/odds")

    def get_scores(self, sport: str, days_from: int = 1) -> Optional[List[Dict]]:
        """Get scores for a sport.

        Args:
            sport: The sport key (e.g., 'basketball_nba')
            days_from: Number of days from today to include
        """
        params = {"daysFrom": days_from}
        return self._make_request(f"sports/{sport}/scores", params)

    def get_events(self, sport: str) -> Optional[List[Dict]]:
        """Get events for a sport.

        Args:
            sport: The sport key (e.g., 'basketball_nba')
        """
        current_time = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        params = {"commence_time": current_time}
        return self._make_request(f"sports/{sport}/events", params)

    def get_event_odds(self, sport: str, event_id: str) -> Optional[Dict]:
        """Get odds for a specific event.

        Args:
            sport: The sport key (e.g., 'basketball_nba')
            event_id: The unique identifier for the event
        """
        return self._make_request(f"sports/{sport}/events/{event_id}/odds")


# Usage example:
if __name__ == "__main__":
    client = OddsAPI("your_api_key")
    sports = client.get_sports()
    if sports:
        logger.info(f"Available sports: {sports}")
