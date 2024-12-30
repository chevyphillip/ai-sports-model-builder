"""Test script for collecting historical odds data."""

import os
import logging
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import text

from src.data_collection.odds_api_client import OddsAPIClient

# Configure logging
os.makedirs("logs", exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("logs/test_odds_collection.log"),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger(__name__)


def test_odds_collection():
    """Test collecting historical odds data."""
    # Initialize client
    client = OddsAPIClient()

    # Get yesterday's date in ISO8601 format
    yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%dT%H:%M:%SZ")
    logger.info(f"Testing odds collection for {yesterday}")

    # Get odds data for yesterday
    odds_data = client.get_historical_odds(yesterday)
    if not odds_data:
        logger.error("No odds data found")
        return

    logger.info(
        f"Successfully retrieved odds data snapshot from {odds_data['timestamp']}"
    )
    logger.info(f"Number of games in snapshot: {len(odds_data['data'])}")

    # Log sample game data
    if odds_data["data"]:
        game = odds_data["data"][0]
        logger.info("\nSample game data:")
        logger.info(f"Game: {game['away_team']} @ {game['home_team']}")
        logger.info(f"Start time: {game['commence_time']}")

        # Log sample odds from DraftKings
        draftkings = next(
            (b for b in game["bookmakers"] if b["key"] == "draftkings"), None
        )
        if draftkings:
            logger.info("\nSample odds from DraftKings:")
            for market in draftkings["markets"]:
                logger.info(f"\nMarket: {market['key']}")
                for outcome in market["outcomes"]:
                    logger.info(f"{outcome['name']}: {outcome['price']}")

    # Test storing the data
    logger.info("\nTesting data storage...")
    with Session(client.engine) as session:
        client.store_odds_snapshot(odds_data, session)

        # Query and log stored data
        logger.info("\nVerifying stored data:")
        query = text(
            """
            SELECT 
                g.game_id,
                g.game_date,
                g.visitor_team,
                g.home_team,
                os.snapshot_timestamp,
                bo.bookmaker_key,
                bo.markets->0->>'key' as market_type
            FROM nba_game_lines.games g
            JOIN nba_game_lines.odds_snapshots os ON g.game_id = os.game_id
            JOIN nba_game_lines.bookmaker_odds bo ON os.id = bo.snapshot_id
            ORDER BY g.game_date DESC
            LIMIT 5
        """
        )

        result = session.execute(query)
        for row in result:
            logger.info(
                f"Game: {row.game_id} - {row.visitor_team} @ {row.home_team} "
                f"({row.game_date.strftime('%Y-%m-%d %H:%M:%S')})"
            )
            logger.info(f"Bookmaker: {row.bookmaker_key}, Market: {row.market_type}")
            logger.info("-" * 80)


if __name__ == "__main__":
    test_odds_collection()
