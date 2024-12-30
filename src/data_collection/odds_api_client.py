"""Client for collecting historical odds data from the Odds API."""

import json
import os
from datetime import datetime, timezone
from typing import Dict, List, Optional
import logging

import requests
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session
from urllib.parse import quote_plus

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class OddsAPIClient:
    """Client for interacting with the Odds API."""

    BASE_URL = "https://api.the-odds-api.com/v4/historical"
    SPORT = "basketball_nba"
    REGIONS = ["us"]  # Focus on US bookmakers
    MARKETS = ["h2h", "spreads", "totals"]  # Markets we want to collect

    def __init__(self, api_key: Optional[str] = None):
        """Initialize the Odds API client.

        Args:
            api_key: Optional API key. If not provided, will try to get from environment.
        """
        self.api_key = api_key or os.getenv("ODDS_API_KEY")
        if not self.api_key:
            raise ValueError("Odds API key not provided and not found in environment")

        # Set up database connection
        db_url = f"postgresql://{os.getenv('DB_USER')}:{quote_plus(os.getenv('DB_PASSWORD'))}@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"
        self.engine = create_engine(db_url, connect_args={"sslmode": "require"})

    def get_historical_odds(
        self,
        date: str,
        sport: str = SPORT,
        regions: List[str] = None,
        markets: List[str] = None,
    ) -> Dict:
        """Get historical odds data for a specific date.

        Args:
            date: ISO8601 formatted date string (e.g., "2024-12-27T12:00:00Z")
            sport: Sport key (default: basketball_nba)
            regions: List of regions to get odds for (default: ["us"])
            markets: List of markets to get odds for (default: ["h2h", "spreads", "totals"])

        Returns:
            Dictionary containing the odds data
        """
        regions = regions or self.REGIONS
        markets = markets or self.MARKETS

        url = f"{self.BASE_URL}/sports/{sport}/odds"
        params = {
            "apiKey": self.api_key,
            "regions": ",".join(regions),
            "markets": ",".join(markets),
            "date": date,
            "oddsFormat": "american",  # Use American odds format
        }

        try:
            response = requests.get(url, params=params)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching odds data: {e}")
            return {}

    def store_odds_snapshot(self, snapshot_data: Dict, session: Session) -> None:
        """Store odds snapshot in the database.

        Args:
            snapshot_data: Odds data from the API
            session: SQLAlchemy session
        """
        try:
            # Store each game's odds
            for game in snapshot_data.get("data", []):
                # Generate game_id in our format: NBA-YYYY-MM-DD-HOME-AWAY
                game_date = datetime.fromisoformat(
                    game["commence_time"].replace("Z", "+00:00")
                )
                home_abbr = "".join(
                    c for c in game["home_team"].upper() if c.isalpha()
                )[:3]
                away_abbr = "".join(
                    c for c in game["away_team"].upper() if c.isalpha()
                )[:3]
                game_id = (
                    f"NBA-{game_date.strftime('%Y-%m-%d')}-{home_abbr}-{away_abbr}"
                )

                # Create game record if it doesn't exist
                game_query = text(
                    """
                    INSERT INTO nba_game_lines.games (
                        game_id, game_date, season_year, season,
                        visitor_team, visitor_points, home_team, home_points,
                        arena, source, scraped_at
                    )
                    VALUES (
                        :game_id, :game_date, :season_year, :season,
                        :visitor_team, 0, :home_team, 0,
                        'TBD', 'odds_api', :scraped_at
                    )
                    ON CONFLICT (game_id) DO NOTHING
                """
                )

                season_year = game_date.year
                season = f"{season_year-1}-{str(season_year)[2:]}"

                session.execute(
                    game_query,
                    {
                        "game_id": game_id,
                        "game_date": game_date,
                        "season_year": season_year,
                        "season": season,
                        "visitor_team": game["away_team"],
                        "home_team": game["home_team"],
                        "scraped_at": datetime.now(timezone.utc),
                    },
                )

                # Create odds snapshot record
                snapshot_query = text(
                    """
                    INSERT INTO nba_game_lines.odds_snapshots (
                        game_id, snapshot_timestamp, 
                        previous_snapshot_timestamp, next_snapshot_timestamp
                    )
                    VALUES (
                        :game_id, :snapshot_timestamp,
                        :previous_snapshot_timestamp, :next_snapshot_timestamp
                    )
                    RETURNING id
                """
                )

                # Insert snapshot and get its ID
                snapshot_id = session.execute(
                    snapshot_query,
                    {
                        "game_id": game_id,
                        "snapshot_timestamp": datetime.fromisoformat(
                            snapshot_data["timestamp"].replace("Z", "+00:00")
                        ),
                        "previous_snapshot_timestamp": (
                            datetime.fromisoformat(
                                snapshot_data["previous_timestamp"].replace(
                                    "Z", "+00:00"
                                )
                            )
                            if snapshot_data.get("previous_timestamp")
                            else None
                        ),
                        "next_snapshot_timestamp": (
                            datetime.fromisoformat(
                                snapshot_data["next_timestamp"].replace("Z", "+00:00")
                            )
                            if snapshot_data.get("next_timestamp")
                            else None
                        ),
                    },
                ).scalar()

                # Store bookmaker odds for this game
                for bookmaker in game.get("bookmakers", []):
                    bookmaker_query = text(
                        """
                        INSERT INTO nba_game_lines.bookmaker_odds (
                            snapshot_id, bookmaker_key, bookmaker_title,
                            last_update, markets
                        )
                        VALUES (
                            :snapshot_id, :bookmaker_key, :bookmaker_title,
                            :last_update, cast(:markets as jsonb)
                        )
                    """
                    )

                    session.execute(
                        bookmaker_query,
                        {
                            "snapshot_id": snapshot_id,
                            "bookmaker_key": bookmaker["key"],
                            "bookmaker_title": bookmaker["title"],
                            "last_update": datetime.fromisoformat(
                                bookmaker["last_update"].replace("Z", "+00:00")
                            ),
                            "markets": json.dumps(bookmaker["markets"]),
                        },
                    )

            session.commit()
            logger.info(
                f"Successfully stored odds snapshot from {snapshot_data['timestamp']}"
            )

        except Exception as e:
            session.rollback()
            logger.error(f"Error storing odds data: {e}")
            raise

    def collect_historical_odds(self, start_date: str, end_date: str) -> None:
        """Collect historical odds data for a date range.

        Args:
            start_date: ISO8601 formatted start date
            end_date: ISO8601 formatted end date
        """
        current_date = start_date

        while current_date <= end_date:
            try:
                # Get odds data for current date
                odds_data = self.get_historical_odds(current_date)
                if not odds_data:
                    logger.warning(f"No odds data found for {current_date}")
                    continue

                # Store the data
                with Session(self.engine) as session:
                    self.store_odds_snapshot(odds_data, session)

                # Move to next snapshot using the next_timestamp from the response
                current_date = odds_data.get("next_timestamp")
                if not current_date or current_date > end_date:
                    break

            except Exception as e:
                logger.error(f"Error processing date {current_date}: {e}")
                continue
