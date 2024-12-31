"""Client for The Odds API."""

import os
import logging
from typing import Dict, Optional, Tuple, List
import requests
import aiohttp
from datetime import datetime, timedelta
import asyncio


class OddsAPIClient:
    """Client for The Odds API."""

    def __init__(self, api_key: Optional[str] = None):
        """Initialize the client.

        Args:
            api_key: API key for The Odds API. If not provided, will try to get from environment.
        """
        self.api_key = api_key or os.getenv("ODDS_API_KEY")
        if not self.api_key:
            raise ValueError(
                "API key must be provided or set in ODDS_API_KEY environment variable"
            )

        self.base_url = "https://api.the-odds-api.com/v4"
        self.sport = "basketball_nba"
        self.regions = "us"
        self.markets = "h2h,spreads,totals"
        self.odds_format = "american"
        self.rate_limit_delay = 0.05  # 50ms delay between requests (20 requests/sec)

    def _build_historical_url(self, date: str) -> str:
        """Build URL for historical odds endpoint.

        Args:
            date: ISO8601 formatted date

        Returns:
            Complete URL for the request
        """
        return (
            f"{self.base_url}/historical/sports/{self.sport}/odds/"
            f"?apiKey={self.api_key}"
            f"&regions={self.regions}"
            f"&markets={self.markets}"
            f"&oddsFormat={self.odds_format}"
            f"&date={date}"
        )

    async def _get_snapshot(
        self, session: aiohttp.ClientSession, timestamp: str
    ) -> Tuple[Dict, Optional[str]]:
        """Get a single odds snapshot for a timestamp.

        Args:
            session: aiohttp ClientSession
            timestamp: ISO8601 formatted timestamp

        Returns:
            Tuple of (data, error)
        """
        url = self._build_historical_url(timestamp)
        await asyncio.sleep(self.rate_limit_delay)

        try:
            async with session.get(url) as response:
                remaining = response.headers.get("x-requests-remaining")
                used = response.headers.get("x-requests-used")

                if remaining and used:
                    logging.debug(
                        f"API Requests - Remaining: {remaining}, Used: {used}"
                    )

                if response.status != 200:
                    text = await response.text()
                    if "EXCEEDED_FREQ_LIMIT" in text:
                        # Add extra delay and retry
                        await asyncio.sleep(1)
                        return await self._get_snapshot(session, timestamp)
                    return {}, f"API Error: {response.status} - {text}"

                data = await response.json()
                return data, None

        except Exception as e:
            return {}, f"Request Error: {str(e)}"

    def _is_same_day(self, timestamp1: str, timestamp2: str) -> bool:
        """Check if two timestamps are from the same day.

        Args:
            timestamp1: First ISO8601 timestamp
            timestamp2: Second ISO8601 timestamp

        Returns:
            True if timestamps are from the same day
        """
        dt1 = datetime.fromisoformat(timestamp1.replace("Z", "+00:00"))
        dt2 = datetime.fromisoformat(timestamp2.replace("Z", "+00:00"))
        return dt1.date() == dt2.date()

    async def _follow_timestamp_chain(
        self,
        session: aiohttp.ClientSession,
        start_timestamp: str,
        max_snapshots: int = 10,
        visited: Optional[set] = None,
    ) -> List[Dict]:
        """Follow the chain of timestamps to collect all snapshots.

        Args:
            session: aiohttp ClientSession
            start_timestamp: Starting ISO8601 timestamp
            max_snapshots: Maximum number of snapshots to collect
            visited: Set of visited timestamps

        Returns:
            List of snapshot data
        """
        snapshots = []
        visited = visited or set()
        queue = [(start_timestamp, 0)]  # (timestamp, depth)

        while queue and len(snapshots) < max_snapshots:
            current_timestamp, depth = queue.pop(0)

            if current_timestamp in visited:
                continue

            visited.add(current_timestamp)
            data, error = await self._get_snapshot(session, current_timestamp)

            if error:
                logging.error(f"Error following timestamp chain: {error}")
                continue

            if not data:
                continue

            if data.get("data"):
                snapshots.append(data)
                logging.info(f"Found {len(data['data'])} games at {current_timestamp}")

            if depth < max_snapshots:
                # Only follow next_timestamp if it exists and is from the same day
                if data.get("next_timestamp"):
                    next_ts = data["next_timestamp"]
                    if next_ts not in visited and self._is_same_day(
                        start_timestamp, next_ts
                    ):
                        queue.append((next_ts, depth + 1))

        return snapshots

    async def get_historical_odds_async(
        self, session: aiohttp.ClientSession, date: str, max_snapshots: int = 10
    ) -> Tuple[List[Dict], Optional[str]]:
        """Get historical odds for a specific date by following timestamp chain.

        Args:
            session: aiohttp ClientSession
            date: ISO8601 formatted date
            max_snapshots: Maximum number of snapshots to collect per date

        Returns:
            Tuple of (list of snapshots, error)
        """
        visited = set()
        all_snapshots = []

        # Get initial snapshot
        data, error = await self._get_snapshot(session, date)
        if error:
            return [], error

        if not data:
            return [], None

        # If we found games, follow the timestamp chain
        if data.get("data"):
            snapshots = await self._follow_timestamp_chain(
                session, date, max_snapshots=max_snapshots, visited=visited
            )
            all_snapshots.extend(snapshots)
            return all_snapshots, None

        # If no games in initial snapshot, try following next_timestamp
        if data.get("next_timestamp"):
            next_ts = data["next_timestamp"]
            if self._is_same_day(date, next_ts):
                snapshots = await self._follow_timestamp_chain(
                    session,
                    next_ts,
                    max_snapshots=max_snapshots,
                    visited=visited,
                )
                all_snapshots.extend(snapshots)
                if all_snapshots:
                    return all_snapshots, None

        return [], None

    def get_historical_odds(self, date: str) -> Tuple[Dict, Optional[str]]:
        """Get historical odds for a specific date (synchronous version).

        Args:
            date: ISO8601 formatted date

        Returns:
            Tuple of (data, error)
        """
        url = self._build_historical_url(date)

        try:
            response = requests.get(url)
            remaining = response.headers.get("x-requests-remaining")
            used = response.headers.get("x-requests-used")

            if remaining and used:
                logging.info(f"API Requests - Remaining: {remaining}, Used: {used}")

            if response.status_code != 200:
                return {}, f"API Error: {response.status_code} - {response.text}"

            return response.json(), None

        except Exception as e:
            return {}, f"Request Error: {str(e)}"
