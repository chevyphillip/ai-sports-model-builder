"""Collector for live and upcoming odds data."""

# Standard library imports
import asyncio
import logging
from datetime import datetime
from typing import Dict, List, Optional

# Third-party imports
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

# Local imports
from ..clients.odds_api_client import OddsAPIClient, OddsAPIRateLimitError
from ..models.game import Game, GameOdds, Bookmaker, Team, MarketType
from ..utils.database import get_db_session

# Initialize logger
logger = logging.getLogger(__name__)


class LiveOddsCollector:
    """Collector for live and upcoming odds data with built-in caching and error handling."""

    def __init__(
        self,
        session: Optional[Session] = None,
        collection_interval: int = 300,  # 5 minutes
        max_retries: int = 3,
    ):
        """Initialize the collector.

        Args:
            session: Database session
            collection_interval: Interval between collections in seconds
            max_retries: Maximum number of retries for failed operations
        """
        self.client = OddsAPIClient()
        self.session = session or get_db_session()
        self.collection_interval = collection_interval
        self.max_retries = max_retries
        self._bookmaker_cache = {}
        self._team_cache = {}
        self.collection_stats = {
            "processed_games": 0,
            "new_games": 0,
            "updated_odds": 0,
            "errors": 0,
            "api_calls": 0,
        }

    def _get_or_create_team(self, name: str) -> Optional[Team]:
        """Get a team from cache or database, create if doesn't exist.

        Args:
            name: Team name

        Returns:
            Team object or None if error
        """
        if name in self._team_cache:
            return self._team_cache[name]

        team = self.session.query(Team).filter(Team.name == name).first()
        if not team:
            try:
                team = Team(name=name)
                self.session.add(team)
                self.session.flush()
                logger.info(f"Created new team: {name}")
            except SQLAlchemyError as e:
                logger.error(f"Error creating team {name}: {str(e)}")
                return None

        self._team_cache[name] = team
        return team

    def _get_bookmaker(self, key: str) -> Optional[Bookmaker]:
        """Get a bookmaker from cache or database.

        Args:
            key: Bookmaker key

        Returns:
            Bookmaker object or None if not found
        """
        if key in self._bookmaker_cache:
            return self._bookmaker_cache[key]

        bookmaker = self.session.query(Bookmaker).filter(Bookmaker.key == key).first()
        if bookmaker:
            self._bookmaker_cache[key] = bookmaker

        return bookmaker

    async def _process_game_odds(
        self, game: Game, odds_data: Dict, timestamp: datetime
    ) -> None:
        """Process and store odds for a game.

        Args:
            game: Game object
            odds_data: Odds data from API
            timestamp: Collection timestamp
        """
        for bm_data in odds_data.get("bookmakers", []):
            bookmaker = self._get_bookmaker(bm_data["key"])
            if not bookmaker:
                logger.warning(f"Unknown bookmaker: {bm_data['key']}")
                continue

            for market_data in bm_data.get("markets", []):
                try:
                    market_type = MarketType(market_data["key"])
                except ValueError:
                    logger.warning(f"Unknown market type: {market_data['key']}")
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

                try:
                    self._create_odds(
                        game, bookmaker, market_type, market_data, timestamp
                    )
                    self.collection_stats["updated_odds"] += 1
                except SQLAlchemyError as e:
                    logger.error(f"Error creating odds for game {game.id}: {str(e)}")
                    self.collection_stats["errors"] += 1

    def _create_odds(
        self,
        game: Game,
        bookmaker: Bookmaker,
        market_type: MarketType,
        market_data: Dict,
        timestamp: datetime,
    ) -> None:
        """Create new odds record.

        Args:
            game: Game object
            bookmaker: Bookmaker object
            market_type: Market type
            market_data: Market data from API
            timestamp: Collection timestamp
        """
        outcomes = {o["name"]: o for o in market_data.get("outcomes", [])}

        if market_type == MarketType.H2H:
            home_data = outcomes.get(game.home_team.name, {})
            away_data = outcomes.get(game.away_team.name, {})

            if home_data and away_data:
                odds = GameOdds(
                    game_id=game.id,
                    bookmaker_id=bookmaker.id,
                    market_type=market_type,
                    timestamp=timestamp,
                    home_price=home_data["price"],
                    away_price=away_data["price"],
                )
                self.session.add(odds)

        elif market_type == MarketType.SPREAD:
            home_data = outcomes.get(game.home_team.name, {})
            away_data = outcomes.get(game.away_team.name, {})

            if home_data and away_data and "point" in home_data:
                odds = GameOdds(
                    game_id=game.id,
                    bookmaker_id=bookmaker.id,
                    market_type=market_type,
                    timestamp=timestamp,
                    home_price=home_data["price"],
                    away_price=away_data["price"],
                    spread=home_data["point"],
                )
                self.session.add(odds)

        elif market_type == MarketType.TOTAL:
            over_data = outcomes.get("Over", {})
            under_data = outcomes.get("Under", {})

            if over_data and under_data and "point" in over_data:
                odds = GameOdds(
                    game_id=game.id,
                    bookmaker_id=bookmaker.id,
                    market_type=market_type,
                    timestamp=timestamp,
                    over_price=over_data["price"],
                    under_price=under_data["price"],
                    total=over_data["point"],
                )
                self.session.add(odds)

    async def collect_current_odds(self) -> None:
        """Collect current odds for all active games."""
        try:
            odds_data = await self.client.get_odds()
            self.collection_stats["api_calls"] += 1

            timestamp = datetime.utcnow()

            for game_data in odds_data:
                try:
                    home_team = self._get_or_create_team(game_data["home_team"])
                    away_team = self._get_or_create_team(game_data["away_team"])

                    if not home_team or not away_team:
                        continue

                    game = (
                        self.session.query(Game)
                        .filter(Game.game_id == game_data["id"])
                        .first()
                    )

                    if not game:
                        game = Game(
                            game_id=game_data["id"],
                            home_team_id=home_team.id,
                            away_team_id=away_team.id,
                            commence_time=datetime.fromisoformat(
                                game_data["commence_time"].replace("Z", "+00:00")
                            ),
                        )
                        self.session.add(game)
                        self.session.flush()
                        self.collection_stats["new_games"] += 1

                    await self._process_game_odds(game, game_data, timestamp)
                    self.collection_stats["processed_games"] += 1

                except SQLAlchemyError as e:
                    logger.error(f"Database error processing game: {str(e)}")
                    self.collection_stats["errors"] += 1
                    continue

            self.session.commit()
            logger.info(f"Collection stats: {self.collection_stats}")

        except OddsAPIRateLimitError:
            logger.error("Rate limit exceeded")
            self.collection_stats["errors"] += 1
        except Exception as e:
            logger.error(f"Error collecting odds: {str(e)}")
            self.collection_stats["errors"] += 1

    async def run_collection_loop(self) -> None:
        """Run continuous collection loop."""
        while True:
            try:
                await self.collect_current_odds()
            except Exception as e:
                logger.error(f"Collection loop error: {str(e)}")

            await asyncio.sleep(self.collection_interval)
