"""Service for collecting and synchronizing historical NBA game and odds data."""

import os
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Tuple
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from urllib.parse import quote_plus
from dotenv import load_dotenv

from src.services.odds_api_service import OddsAPIService

# Load environment variables
load_dotenv()


class HistoricalDataService:
    """Service for collecting and synchronizing historical NBA game and odds data."""

    def __init__(self):
        """Initialize the service with database connection and API client."""
        # Create database connection
        url = f"postgresql://{os.getenv('DB_USER')}:{quote_plus(os.getenv('DB_PASSWORD'))}@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"
        self.engine = create_engine(url, echo=True, connect_args={"sslmode": "require"})
        self.Session = sessionmaker(bind=self.engine)

        # Initialize API client
        self.odds_api = OddsAPIService()

    def get_existing_games(
        self, start_date: datetime, end_date: datetime
    ) -> List[Dict]:
        """Get existing games from the database within a date range.

        Args:
            start_date: Start date for the query
            end_date: End date for the query

        Returns:
            List of games from the database
        """
        query = text(
            """
            SELECT 
                game_id,
                game_date,
                home_team_name,
                visitor_team_name,
                home_points,
                visitor_points
            FROM nba_game_lines.nba_games
            WHERE game_date BETWEEN :start_date AND :end_date
            ORDER BY game_date
        """
        )

        with self.engine.connect() as conn:
            result = conn.execute(
                query, {"start_date": start_date, "end_date": end_date}
            )
            return [
                {
                    "game_id": row.game_id,
                    "game_date": row.game_date,
                    "home_team_name": row.home_team_name,
                    "visitor_team_name": row.visitor_team_name,
                    "home_points": row.home_points,
                    "visitor_points": row.visitor_points,
                }
                for row in result
            ]

    def get_games_from_api(self, date: datetime) -> List[Dict]:
        """Get games from The Odds API for a specific date.

        Args:
            date: The date to get games for

        Returns:
            List of games from the API
        """
        try:
            print(f"\n🔍 Fetching games from API for {date.date()}")
            # Get historical games data
            games_data = self.odds_api.get_historical_games(date)

            if not games_data.get("data"):
                print("  ⚠️  No games data returned from API")
                return []

            print(f"  ✅ Found {len(games_data['data'])} games in API response")
            return games_data["data"]
        except Exception as e:
            print(f"❌ Error getting games from API: {str(e)}")
            return []

    def find_matching_game(
        self, api_game: Dict, db_games: List[Dict]
    ) -> Optional[Dict]:
        """Find a matching game in our database for an API game.

        Args:
            api_game: Game data from the API
            db_games: List of games from our database

        Returns:
            Matching game from our database, if found
        """
        # Team name mapping from The Odds API to our database
        team_name_mapping = {
            # Full names
            "Los Angeles Lakers": "Los Angeles Lakers",
            "LA Clippers": "Los Angeles Clippers",
            "LA Lakers": "Los Angeles Lakers",
            "Golden State Warriors": "Golden State",
            "Portland Trail Blazers": "Portland",
            "Oklahoma City Thunder": "Oklahoma City",
            "New Orleans Pelicans": "New Orleans",
            "San Antonio Spurs": "San Antonio",
            "New York Knicks": "New York",
            "Brooklyn Nets": "Brooklyn",
            "Philadelphia 76ers": "Philadelphia",
            "Minnesota Timberwolves": "Minnesota",
            "Memphis Grizzlies": "Memphis",
            "Sacramento Kings": "Sacramento",
            "Phoenix Suns": "Phoenix",
            "Orlando Magic": "Orlando",
            "Toronto Raptors": "Toronto",
            "Cleveland Cavaliers": "Cleveland",
            "Houston Rockets": "Houston",
            "Detroit Pistons": "Detroit",
            "Milwaukee Bucks": "Milwaukee",
            "Indiana Pacers": "Indiana",
            "Denver Nuggets": "Denver",
            "Charlotte Hornets": "Charlotte",
            "Utah Jazz": "Utah",
            "Dallas Mavericks": "Dallas",
            "Miami Heat": "Miami",
            "Chicago Bulls": "Chicago",
            "Boston Celtics": "Boston",
            # Short names
            "76ers": "Philadelphia",
            "blazers": "Portland",
            "bucks": "Milwaukee",
            "bulls": "Chicago",
            "cavaliers": "Cleveland",
            "celtics": "Boston",
            "clippers": "Los Angeles Clippers",
            "grizzlies": "Memphis",
            "hawks": "Atlanta",
            "heat": "Miami",
            "hornets": "Charlotte",
            "jazz": "Utah",
            "kings": "Sacramento",
            "knicks": "New York",
            "lakers": "Los Angeles Lakers",
            "magic": "Orlando",
            "mavericks": "Dallas",
            "nets": "Brooklyn",
            "nuggets": "Denver",
            "pacers": "Indiana",
            "pelicans": "New Orleans",
            "pistons": "Detroit",
            "raptors": "Toronto",
            "rockets": "Houston",
            "spurs": "San Antonio",
            "suns": "Phoenix",
            "thunder": "Oklahoma City",
            "timberwolves": "Minnesota",
            "trail blazers": "Portland",
            "warriors": "Golden State",
            "wizards": "Washington",
        }

        api_date = datetime.fromisoformat(
            api_game["commence_time"].replace("Z", "+00:00")
        )
        api_home = api_game["home_team"]  # Keep original case for mapping
        api_away = api_game["away_team"]  # Keep original case for mapping

        # Try to map team names
        mapped_home = team_name_mapping.get(api_home, api_home)
        mapped_away = team_name_mapping.get(api_away, api_away)

        print(f"\n🔍 Looking for game match:")
        print(f"  API Game: {api_away} @ {api_home}")
        print(f"  Mapped to: {mapped_away} @ {mapped_home}")
        print(f"  Date: {api_date}")

        for game in db_games:
            db_date = game["game_date"]
            db_home = game["home_team_name"].lower()
            db_away = game["visitor_team_name"].lower()

            # Check if team names match
            home_match = (
                mapped_home.lower() in db_home or db_home in mapped_home.lower()
            )
            away_match = (
                mapped_away.lower() in db_away or db_away in mapped_away.lower()
            )
            teams_match = home_match and away_match

            # Check if dates are within 24 hours and on the same day
            time_diff = abs(api_date - db_date)
            same_day = api_date.date() == db_date.date()
            dates_match = time_diff < timedelta(hours=24) and same_day

            print(f"  Checking against DB game: {db_away} @ {db_home} at {db_date}")
            print(
                f"    Teams match: {teams_match} (Home: {home_match}, Away: {away_match})"
            )
            print(
                f"    Dates match: {dates_match} (Time diff: {time_diff}, Same day: {same_day})"
            )

            if teams_match and dates_match:
                print(f"  ✅ Found matching game!")
                return game

        print("  ❌ No matching game found")
        return None

    def create_odds_snapshot(
        self,
        api_game_id: str,
        snapshot_timestamp: datetime,
        previous_snapshot_timestamp: Optional[datetime] = None,
        next_snapshot_timestamp: Optional[datetime] = None,
    ) -> str:
        """Create a new odds snapshot record.

        Args:
            api_game_id: The game ID from The Odds API
            snapshot_timestamp: Timestamp of the snapshot
            previous_snapshot_timestamp: Timestamp of the previous snapshot
            next_snapshot_timestamp: Timestamp of the next snapshot

        Returns:
            The ID of the created snapshot
        """
        query = text(
            """
            INSERT INTO nba_game_lines.odds_snapshots (
                game_id,
                snapshot_timestamp,
                previous_snapshot_timestamp,
                next_snapshot_timestamp,
                created_at
            )
            VALUES (
                :game_id,
                :snapshot_timestamp,
                :previous_snapshot_timestamp,
                :next_snapshot_timestamp,
                CURRENT_TIMESTAMP
            )
            RETURNING id
        """
        )

        with self.engine.connect() as conn:
            result = conn.execute(
                query,
                {
                    "game_id": api_game_id,
                    "snapshot_timestamp": snapshot_timestamp,
                    "previous_snapshot_timestamp": previous_snapshot_timestamp,
                    "next_snapshot_timestamp": next_snapshot_timestamp,
                },
            )
            conn.commit()
            return str(result.scalar())

    def store_odds(self, snapshot_id: str, odds_data: Dict) -> None:
        """Store odds data for a snapshot.

        Args:
            snapshot_id: ID of the odds snapshot
            odds_data: Odds data from the API
        """
        query = text(
            """
            INSERT INTO nba_game_lines.game_odds (
                game_id,
                snapshot_id,
                bookmaker_key,
                bookmaker_title,
                home_spread,
                away_spread,
                home_spread_odds,
                away_spread_odds,
                home_moneyline,
                away_moneyline,
                over_under,
                over_odds,
                under_odds,
                markets,
                odds_updated_at
            )
            VALUES (
                :game_id,
                :snapshot_id,
                :bookmaker_key,
                :bookmaker_title,
                :home_spread,
                :away_spread,
                :home_spread_odds,
                :away_spread_odds,
                :home_moneyline,
                :away_moneyline,
                :over_under,
                :over_odds,
                :under_odds,
                :markets,
                :odds_updated_at
            )
        """
        )

        with self.engine.connect() as conn:
            for bookmaker in odds_data.get("bookmakers", []):
                markets_data = {}
                home_spread = away_spread = None
                home_spread_odds = away_spread_odds = None
                home_moneyline = away_moneyline = None
                over_under = over_odds = under_odds = None

                for market in bookmaker.get("markets", []):
                    markets_data[market["key"]] = market

                    if market["key"] == "spreads":
                        for outcome in market.get("outcomes", []):
                            if outcome["name"] == odds_data["home_team"]:
                                home_spread = outcome.get("point")
                                home_spread_odds = outcome.get("price")
                            else:
                                away_spread = outcome.get("point")
                                away_spread_odds = outcome.get("price")

                    elif market["key"] == "h2h":
                        for outcome in market.get("outcomes", []):
                            if outcome["name"] == odds_data["home_team"]:
                                home_moneyline = outcome.get("price")
                            else:
                                away_moneyline = outcome.get("price")

                    elif market["key"] == "totals":
                        over_under = next(
                            (
                                o.get("point")
                                for o in market.get("outcomes", [])
                                if o["name"] == "Over"
                            ),
                            None,
                        )
                        over_odds = next(
                            (
                                o.get("price")
                                for o in market.get("outcomes", [])
                                if o["name"] == "Over"
                            ),
                            None,
                        )
                        under_odds = next(
                            (
                                o.get("price")
                                for o in market.get("outcomes", [])
                                if o["name"] == "Under"
                            ),
                            None,
                        )

                conn.execute(
                    query,
                    {
                        "game_id": odds_data["id"],
                        "snapshot_id": snapshot_id,
                        "bookmaker_key": bookmaker["key"],
                        "bookmaker_title": bookmaker["title"],
                        "home_spread": home_spread,
                        "away_spread": away_spread,
                        "home_spread_odds": home_spread_odds,
                        "away_spread_odds": away_spread_odds,
                        "home_moneyline": home_moneyline,
                        "away_moneyline": away_moneyline,
                        "over_under": over_under,
                        "over_odds": over_odds,
                        "under_odds": under_odds,
                        "markets": markets_data,
                        "odds_updated_at": bookmaker.get("last_update"),
                    },
                )
            conn.commit()

    def collect_historical_odds(
        self, start_date: datetime, end_date: datetime, interval_minutes: int = 5
    ) -> None:
        """Collect historical odds data for games within a date range.

        Args:
            start_date: Start date for data collection
            end_date: End date for data collection
            interval_minutes: Time interval between odds snapshots in minutes
        """
        print("\n📅 Date Range:")
        print(f"  Start: {start_date}")
        print(f"  End: {end_date}")
        print(f"  Interval: {interval_minutes} minutes")

        # Extend the date range by one day to handle UTC day boundaries
        extended_end_date = end_date + timedelta(days=1)
        print(f"  Extended end date: {extended_end_date} (to handle UTC boundaries)")

        # Get existing games from database
        db_games = self.get_existing_games(start_date, extended_end_date)
        print(f"\n📊 Found {len(db_games)} games in the database:")
        for game in db_games:
            print(
                f"  {game['game_date']}: {game['visitor_team_name']} @ {game['home_team_name']}"
            )

        # Process each day in the range
        current_date = start_date
        while current_date <= extended_end_date:
            print(f"\n📆 Processing date: {current_date.date()}")

            try:
                # Get historical odds for this timestamp
                print(f"\n  📊 Getting odds snapshot for {current_date}")
                odds_data = self.odds_api.get_historical_odds(current_date)

                if not odds_data.get("data"):
                    print("  ⚠️  No odds data available")
                    current_date += timedelta(minutes=interval_minutes)
                    continue

                print(f"  ✅ Found odds data with {len(odds_data['data'])} games")
                print(f"  📅 Snapshot timestamp: {odds_data['timestamp']}")
                if odds_data.get("previous_timestamp"):
                    print(f"  ⬅️  Previous snapshot: {odds_data['previous_timestamp']}")
                if odds_data.get("next_timestamp"):
                    print(f"  ➡️  Next snapshot: {odds_data['next_timestamp']}")

                # Process each game in the odds data
                for game_odds in odds_data["data"]:
                    print(
                        f"\n🎯 Processing game: {game_odds['away_team']} @ {game_odds['home_team']}"
                    )

                    # Find matching game in our database
                    db_game = self.find_matching_game(game_odds, db_games)
                    if not db_game:
                        print(f"  ❌ No matching game found in database")
                        continue

                    print(
                        f"  ✅ Found matching game: {db_game['visitor_team_name']} @ {db_game['home_team_name']}"
                    )

                    # Create snapshot record
                    snapshot_id = self.create_odds_snapshot(
                        api_game_id=game_odds["id"],
                        snapshot_timestamp=datetime.fromisoformat(
                            odds_data["timestamp"].replace("Z", "+00:00")
                        ),
                        previous_snapshot_timestamp=(
                            datetime.fromisoformat(
                                odds_data["previous_timestamp"].replace("Z", "+00:00")
                            )
                            if odds_data.get("previous_timestamp")
                            else None
                        ),
                        next_snapshot_timestamp=(
                            datetime.fromisoformat(
                                odds_data["next_timestamp"].replace("Z", "+00:00")
                            )
                            if odds_data.get("next_timestamp")
                            else None
                        ),
                    )

                    # Store odds data
                    self.store_odds(snapshot_id, game_odds)
                    print(f"  💾 Stored odds snapshot")

                # Use the next timestamp from the API response if available
                if odds_data.get("next_timestamp"):
                    next_time = datetime.fromisoformat(
                        odds_data["next_timestamp"].replace("Z", "+00:00")
                    )
                    print(f"\n⏭️  Moving to next available timestamp: {next_time}")
                    current_date = next_time
                else:
                    current_date += timedelta(minutes=interval_minutes)
                    print(f"\n⏭️  Moving to next interval: {current_date}")

            except Exception as e:
                print(f"❌ Error processing timestamp {current_date}: {str(e)}")
                # Continue with next interval even if this one failed
                current_date += timedelta(minutes=interval_minutes)
                continue

        print("\n✅ Historical odds collection completed")
