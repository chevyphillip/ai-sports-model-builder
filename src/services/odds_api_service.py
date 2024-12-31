"""Service for interacting with The Odds API."""

import os
import requests
from datetime import datetime, timezone
from typing import Dict, Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class OddsAPIService:
    """Service for interacting with The Odds API."""

    def __init__(self):
        """Initialize the service with API configuration."""
        self.api_key = os.getenv("ODDS_API_KEY")
        self.base_url = "https://api.the-odds-api.com/v4"
        self.sport = "basketball_nba"

    def _make_request(self, endpoint: str, params: Dict) -> Dict:
        """Make a request to The Odds API.

        Args:
            endpoint: API endpoint to call
            params: Query parameters for the request

        Returns:
            API response data
        """
        # Add API key to params
        params["apiKey"] = self.api_key

        # Make request
        response = requests.get(f"{self.base_url}{endpoint}", params=params)
        response.raise_for_status()

        # Log remaining requests
        remaining = response.headers.get("x-requests-remaining", "unknown")
        used = response.headers.get("x-requests-used", "unknown")
        print(f"API Requests - Remaining: {remaining}, Used: {used}")

        return response.json()

    def get_historical_odds(self, date: datetime) -> Dict:
        """Get historical odds for NBA games.

        Args:
            date: Date to get odds for

        Returns:
            Historical odds data
        """
        # Convert date to ISO format and ensure UTC timezone
        if date.tzinfo is None:
            date = date.replace(tzinfo=timezone.utc)
        iso_date = date.strftime("%Y-%m-%dT%H:%M:%SZ")

        # Make request
        return self._make_request(
            f"/historical/sports/{self.sport}/odds",
            {
                "date": iso_date,
                "regions": "us",
                "markets": "h2h,spreads,totals",
                "oddsFormat": "american",
            },
        )

    def get_historical_games(self, date: datetime) -> Dict:
        """Get historical games for NBA.

        Args:
            date: Date to get games for

        Returns:
            Historical games data
        """
        # Convert date to ISO format and ensure UTC timezone
        if date.tzinfo is None:
            date = date.replace(tzinfo=timezone.utc)
        iso_date = date.strftime("%Y-%m-%dT%H:%M:%SZ")

        # Make request
        return self._make_request(
            f"/historical/sports/{self.sport}/events",
            {
                "date": iso_date,
            },
        )
