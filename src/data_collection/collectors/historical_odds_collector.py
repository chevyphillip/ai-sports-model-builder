"""Collect historical odds data from The Odds API."""

import os
import logging
import asyncio
from datetime import datetime, timedelta
import json
import aiohttp
from tqdm import tqdm
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from typing import List, Dict, Optional, Set, Tuple

from ..models.game import Game, GameOdds, Bookmaker, Team, MarketType
from ..utils.database import get_db_session
from .odds_api_client import OddsAPIClient


class HistoricalOddsCollector:
    """Collector for historical odds data."""

    def __init__(self, max_concurrent_requests: int = 3):
        """Initialize the collector.

        Args:
            max_concurrent_requests: Maximum number of concurrent API requests
        """
        self.client = OddsAPIClient()
        self.max_concurrent_requests = max_concurrent_requests
        self.session = get_db_session()
        self.visited_timestamps = set()
        self.visited_game_ids = set()
        self.next_day_semaphore = asyncio.Semaphore(
            1
        )  # Only one next-day chain at a time
        self.collection_stats = {
            "total_dates": 0,
            "processed_dates": 0,
            "total_snapshots": 0,
            "total_games": 0,
            "new_games": 0,
            "duplicate_games": 0,
            "errors": 0,
            "next_day_timestamps": 0,
            "rate_limit_retries": 0,
            "skipped_dates": 0,
        }
        self._bookmaker_cache = {}
        self._team_cache = {}

    def _get_bookmaker(self, key: str) -> Optional[Bookmaker]:
        """Get a bookmaker by key.

        Args:
            key: Bookmaker key

        Returns:
            Bookmaker if found, None otherwise
        """
        if key in self._bookmaker_cache:
            return self._bookmaker_cache[key]

        bookmaker = self.session.query(Bookmaker).filter(Bookmaker.key == key).first()

        if bookmaker:
            self._bookmaker_cache[key] = bookmaker

        return bookmaker

    def _get_team_by_name(self, name: str) -> Optional[Team]:
        """Get a team by name.

        Args:
            name: Team name

        Returns:
            Team if found, None otherwise
        """
        if name in self._team_cache:
            return self._team_cache[name]

        team = self.session.query(Team).filter(Team.name == name).first()

        if team:
            self._team_cache[name] = team

        return team

    def _normalize_timestamp(self, ts: str) -> datetime:
        """Normalize timestamp to UTC datetime.

        Args:
            ts: ISO8601 timestamp string

        Returns:
            UTC datetime object
        """
        return datetime.fromisoformat(ts.replace("Z", "+00:00"))

    def _save_to_db(self, snapshot: Dict) -> None:
        """Save a snapshot to the database.

        Args:
            snapshot: Odds API snapshot data
        """
        try:
            timestamp = self._normalize_timestamp(snapshot["timestamp"])

            for game_data in snapshot.get("data", []):
                game_id = game_data["id"]

                # Skip if we've already processed this game
                if game_id in self.visited_game_ids:
                    self.collection_stats["duplicate_games"] += 1
                    continue

                self.visited_game_ids.add(game_id)

                # Get teams
                home_team = self._get_team_by_name(game_data["home_team"])
                away_team = self._get_team_by_name(game_data["away_team"])

                if not home_team or not away_team:
                    logging.error(
                        f"Could not find teams: home={game_data['home_team']}, "
                        f"away={game_data['away_team']}"
                    )
                    continue

                # Check if game already exists
                game = self.session.query(Game).filter(Game.game_id == game_id).first()

                if not game:
                    # Create game
                    game = Game(
                        game_id=game_id,
                        home_team_id=home_team.id,
                        away_team_id=away_team.id,
                        commence_time=self._normalize_timestamp(
                            game_data["commence_time"]
                        ),
                    )
                    self.session.add(game)
                    self.session.flush()  # Get game.id
                    self.collection_stats["new_games"] += 1
                    logging.info(f"Created new game {game_id}")

                # Process bookmakers and odds
                for bm_data in game_data["bookmakers"]:
                    bookmaker = self._get_bookmaker(bm_data["key"])
                    if not bookmaker:
                        logging.warning(f"Skipping unknown bookmaker: {bm_data['key']}")
                        continue

                    for market_data in bm_data["markets"]:
                        try:
                            market_type = MarketType(market_data["key"])
                        except ValueError:
                            logging.warning(
                                f"Unknown market type: {market_data['key']}, skipping"
                            )
                            continue

                        # Check for existing odds
                        existing_odds = (
                            self.session.query(GameOdds)
                            .filter(
                                GameOdds.game_id == game.id,
                                GameOdds.bookmaker_id == bookmaker.id,
                                GameOdds.market_type == market_type,
                                GameOdds.timestamp == timestamp,
                            )
                            .first()
                        )

                        if existing_odds:
                            continue

                        # Process outcomes
                        outcomes = market_data["outcomes"]
                        if market_type == MarketType.H2H:
                            # Moneyline
                            home_price = None
                            away_price = None
                            for outcome in outcomes:
                                if outcome["name"] == game_data["home_team"]:
                                    home_price = outcome["price"]
                                elif outcome["name"] == game_data["away_team"]:
                                    away_price = outcome["price"]

                            if home_price is not None and away_price is not None:
                                odds = GameOdds(
                                    game_id=game.id,
                                    bookmaker_id=bookmaker.id,
                                    market_type=market_type,
                                    timestamp=timestamp,
                                    home_price=home_price,
                                    away_price=away_price,
                                )
                                self.session.add(odds)

                        elif market_type == MarketType.SPREAD:
                            # Point spread
                            home_price = None
                            away_price = None
                            spread = None
                            for outcome in outcomes:
                                if outcome["name"] == game_data["home_team"]:
                                    home_price = outcome["price"]
                                    spread = outcome["point"]
                                elif outcome["name"] == game_data["away_team"]:
                                    away_price = outcome["price"]

                            if all(
                                x is not None for x in [home_price, away_price, spread]
                            ):
                                odds = GameOdds(
                                    game_id=game.id,
                                    bookmaker_id=bookmaker.id,
                                    market_type=market_type,
                                    timestamp=timestamp,
                                    home_price=home_price,
                                    away_price=away_price,
                                    spread=spread,
                                )
                                self.session.add(odds)

                        elif market_type == MarketType.TOTAL:
                            # Over/under
                            over_price = None
                            under_price = None
                            total = None
                            for outcome in outcomes:
                                if outcome["name"] == "Over":
                                    over_price = outcome["price"]
                                    total = outcome["point"]
                                elif outcome["name"] == "Under":
                                    under_price = outcome["price"]

                            if all(
                                x is not None for x in [over_price, under_price, total]
                            ):
                                odds = GameOdds(
                                    game_id=game.id,
                                    bookmaker_id=bookmaker.id,
                                    market_type=market_type,
                                    timestamp=timestamp,
                                    over_price=over_price,
                                    under_price=under_price,
                                    total=total,
                                )
                                self.session.add(odds)

                self.session.commit()

        except SQLAlchemyError as e:
            self.session.rollback()
            logging.error(f"Database error: {str(e)}")
            self.collection_stats["errors"] += 1
            raise

    def _generate_date_range(self, start_year: int, end_year: int) -> List[str]:
        """Generate a list of ISO8601 formatted dates for the specified year range.

        Args:
            start_year: Starting year
            end_year: Ending year (inclusive)

        Returns:
            List of ISO8601 formatted dates
        """
        dates = []
        current_date = datetime(start_year, 1, 1)
        end_date = datetime(end_year + 1, 1, 1)

        while current_date < end_date:
            dates.append(current_date.strftime("%Y-%m-%dT%H:%M:%SZ"))
            current_date += timedelta(days=1)

        return dates

    def _get_next_day_timestamp(self, snapshot: Dict) -> Optional[str]:
        """Get the next day's timestamp from a snapshot.

        Args:
            snapshot: Odds API snapshot data

        Returns:
            Next day's timestamp if found, None otherwise
        """
        if not snapshot:
            return None

        next_ts = snapshot.get("next_timestamp")
        if not next_ts:
            return None

        try:
            # Convert timestamps to datetime objects
            current_dt = self._normalize_timestamp(snapshot["timestamp"])
            next_dt = self._normalize_timestamp(next_ts)

            # If next timestamp is from a different day, return it
            if next_dt.date() > current_dt.date():
                return next_ts

        except (ValueError, KeyError) as e:
            logging.error(f"Error parsing timestamps: {str(e)}")

        return None

    async def _handle_rate_limit(self, error: str) -> bool:
        """Handle rate limit errors.

        Args:
            error: Error message from API

        Returns:
            True if should retry, False otherwise
        """
        if "EXCEEDED_FREQ_LIMIT" in error:
            self.collection_stats["rate_limit_retries"] += 1
            retry_delay = min(
                1 * (2 ** self.collection_stats["rate_limit_retries"]), 30
            )
            logging.warning(f"Rate limit exceeded. Waiting {retry_delay} seconds...")
            await asyncio.sleep(retry_delay)
            return True
        return False

    def _should_skip_date(self, date: str) -> bool:
        """Check if we should skip processing a date.

        Args:
            date: ISO8601 formatted date

        Returns:
            True if we should skip this date
        """
        try:
            date_dt = self._normalize_timestamp(date)
            # Check if we've already processed any timestamps from this date
            for ts in self.visited_timestamps:
                ts_dt = self._normalize_timestamp(ts)
                if ts_dt.date() == date_dt.date():
                    return True
            return False
        except ValueError:
            return False

    async def _process_date(
        self, session: aiohttp.ClientSession, date: str, depth: int = 0
    ) -> None:
        """Process a single date, following timestamp chains and saving to database.

        Args:
            session: aiohttp ClientSession
            date: ISO8601 formatted date
            depth: Current depth in the next-day chain
        """
        # Skip if we've already processed this timestamp
        if date in self.visited_timestamps:
            return

        # Skip if we've already processed this date through a next-day chain
        if self._should_skip_date(date):
            self.collection_stats["skipped_dates"] += 1
            logging.info(
                f"Skipping date {date} - already processed through next-day chain"
            )
            return

        # Limit the depth of next-day chains
        if depth > 5:
            logging.warning(f"Max next-day chain depth reached for {date}")
            return

        self.visited_timestamps.add(date)
        snapshots, error = await self.client.get_historical_odds_async(
            session, date, max_snapshots=10
        )

        if error:
            logging.error(f"Error processing {date}: {error}")
            if await self._handle_rate_limit(error):
                # Remove from visited set to allow retry
                self.visited_timestamps.remove(date)
                await self._process_date(session, date, depth)
            else:
                self.collection_stats["errors"] += 1
            return

        for snapshot in snapshots:
            if snapshot.get("data"):
                self.collection_stats["total_snapshots"] += 1
                self.collection_stats["total_games"] += len(snapshot["data"])
                try:
                    self._save_to_db(snapshot)
                except Exception as e:
                    logging.error(f"Error saving snapshot to database: {str(e)}")
                    self.collection_stats["errors"] += 1

            # Check for next day's timestamp
            if next_day_ts := self._get_next_day_timestamp(snapshot):
                self.collection_stats["next_day_timestamps"] += 1
                logging.info(f"Found next day timestamp: {next_day_ts}")
                # Use semaphore to limit concurrent next-day chains
                async with self.next_day_semaphore:
                    await self._process_date(session, next_day_ts, depth + 1)

    async def collect_historical_odds(
        self, start_year: int = 2020, end_year: int = 2024
    ) -> None:
        """Collect historical odds data for the specified year range.

        Args:
            start_year: Starting year
            end_year: Ending year (inclusive)
        """
        dates = self._generate_date_range(start_year, end_year)
        self.collection_stats["total_dates"] = len(dates)

        async with aiohttp.ClientSession() as session:
            semaphore = asyncio.Semaphore(self.max_concurrent_requests)
            tasks = []

            async def process_with_semaphore(date: str) -> None:
                async with semaphore:
                    await self._process_date(session, date)
                    self.collection_stats["processed_dates"] += 1

            with tqdm(total=len(dates), desc="Collecting historical odds") as pbar:
                for date in dates:
                    task = asyncio.create_task(process_with_semaphore(date))
                    task.add_done_callback(lambda _: pbar.update(1))
                    tasks.append(task)

                await asyncio.gather(*tasks)

        # Save collection stats
        with open("collection_stats.json", "w") as f:
            json.dump(self.collection_stats, f, indent=2)

        logging.info("Collection complete. Stats:")
        for key, value in self.collection_stats.items():
            logging.info(f"{key}: {value}")


async def main():
    """Run the historical odds collector."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
    )

    collector = HistoricalOddsCollector(max_concurrent_requests=3)
    await collector.collect_historical_odds()


if __name__ == "__main__":
    asyncio.run(main())
