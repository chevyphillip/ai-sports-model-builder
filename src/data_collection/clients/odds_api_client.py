"""Client for The Odds API with rate limiting and retry mechanisms."""

# Standard library imports
import asyncio
import logging
import os
import time
from typing import Dict, Optional, Any

# Third-party imports
import aiohttp
from tenacity import retry, stop_after_attempt, wait_exponential

# Initialize logger
logger = logging.getLogger(__name__)


class OddsAPIRateLimitError(Exception):
    """Raised when rate limit is exceeded."""

    pass


class OddsAPIClient:
    """A client for The Odds API with built-in rate limiting and retries."""

    BASE_URL = "https://api.the-odds-api.com/v4/sports"

    def __init__(
        self,
        api_key: Optional[str] = None,
        max_retries: int = 3,
        rate_limit_per_month: int = 500,
        sport: str = "basketball_nba",
    ):
        """Initialize the client.

        Args:
            api_key: API key for The Odds API. Defaults to env var ODDS_API_KEY
            max_retries: Maximum number of retries for failed requests
            rate_limit_per_month: Monthly API request limit
            sport: Sport to fetch odds for
        """
        self.api_key = api_key or os.getenv("ODDS_API_KEY")
        if not self.api_key:
            raise ValueError("API key is required")

        self.sport = sport
        self.max_retries = max_retries
        self.rate_limit_per_month = rate_limit_per_month
        self._request_count = 0
        self._last_request_time = 0
        self._min_request_interval = (
            30 * 24 * 60 * 60
        ) / rate_limit_per_month  # seconds between requests

    async def _wait_for_rate_limit(self) -> None:
        """Ensure we don't exceed rate limits."""
        current_time = time.time()
        time_since_last_request = current_time - self._last_request_time

        if time_since_last_request < self._min_request_interval:
            wait_time = self._min_request_interval - time_since_last_request
            logger.debug(f"Rate limit: waiting {wait_time:.2f} seconds")
            await asyncio.sleep(wait_time)

        self._last_request_time = time.time()
        self._request_count += 1

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        reraise=True,
    )
    async def _make_request(
        self, endpoint: str, params: Optional[Dict[str, Any]] = None
    ) -> Dict:
        """Make a request to the API with retries and error handling.

        Args:
            endpoint: API endpoint
            params: Query parameters

        Returns:
            API response data

        Raises:
            OddsAPIRateLimitError: If rate limit is exceeded
            aiohttp.ClientError: For other API errors
        """
        await self._wait_for_rate_limit()

        url = f"{self.BASE_URL}/{endpoint}"
        params = params or {}
        params["apiKey"] = self.api_key

        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(url, params=params) as response:
                    remaining = int(response.headers.get("X-Requests-Remaining", 0))
                    logger.info(f"Remaining API requests: {remaining}")

                    if response.status == 429:
                        raise OddsAPIRateLimitError("Rate limit exceeded")

                    response.raise_for_status()
                    return await response.json()

            except aiohttp.ClientError as e:
                logger.error(f"API request failed: {str(e)}")
                raise

    async def get_odds(
        self,
        markets: str = "h2h,spreads,totals",
        regions: str = "us",
        odds_format: str = "decimal",
        date_format: str = "iso",
    ) -> Dict:
        """Get current odds for NBA games.

        Args:
            markets: Comma-separated list of markets
            regions: Comma-separated list of regions
            odds_format: Format for odds values
            date_format: Format for dates

        Returns:
            Current odds data
        """
        params = {
            "markets": markets,
            "regions": regions,
            "oddsFormat": odds_format,
            "dateFormat": date_format,
        }

        return await self._make_request(f"{self.sport}/odds", params)

    async def get_scores(self, daysFrom: int = 1, date_format: str = "iso") -> Dict:
        """Get scores for completed games.

        Args:
            daysFrom: Number of days from today
            date_format: Format for dates

        Returns:
            Scores data
        """
        params = {"daysFrom": daysFrom, "dateFormat": date_format}

        return await self._make_request(f"{self.sport}/scores", params)
