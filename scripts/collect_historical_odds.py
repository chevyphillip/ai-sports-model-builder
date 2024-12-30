"""Script for collecting historical odds data from The Odds API."""

import os
import logging
from datetime import datetime, timezone, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import text, create_engine
from urllib.parse import quote_plus
import time
from typing import Optional

from src.data_collection.odds_api_client import OddsAPIClient

# Configure logging
os.makedirs("logs", exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("logs/historical_odds_collection.log"),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger(__name__)

# Constants
HISTORICAL_START_DATE = "2020-06-06T00:00:00Z"  # First available historical data
SNAPSHOT_CHANGE_DATE = (
    "2022-09-01T00:00:00Z"  # Date when snapshot interval changed to 5 minutes
)


def get_last_processed_timestamp() -> Optional[str]:
    """Get the timestamp of the last processed snapshot from the database."""
    db_url = f"postgresql://{os.getenv('DB_USER')}:{quote_plus(os.getenv('DB_PASSWORD'))}@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"
    engine = create_engine(db_url, connect_args={"sslmode": "require"})

    query = text(
        """
        SELECT MAX(snapshot_timestamp) as last_timestamp
        FROM nba_game_lines.odds_snapshots
    """
    )

    with engine.connect() as conn:
        result = conn.execute(query).fetchone()
        if result[0]:
            # Convert to UTC and format as ISO8601
            timestamp = result[0].astimezone(timezone.utc)
            return timestamp.strftime("%Y-%m-%dT%H:%M:%SZ")
        return None


def format_timestamp(timestamp: str) -> str:
    """Format timestamp to ISO8601 format with Z suffix."""
    # Remove any existing timezone info and add Z
    if "+" in timestamp:
        timestamp = timestamp.split("+")[0] + "Z"
    elif timestamp.endswith("Z"):
        return timestamp
    else:
        timestamp = timestamp + "Z"
    return timestamp


def collect_historical_odds():
    """Collect all available historical odds data."""
    client = OddsAPIClient()

    # Get the last processed timestamp or start from the beginning
    start_date = get_last_processed_timestamp() or HISTORICAL_START_DATE
    end_date = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    logger.info(f"Starting historical odds collection from {start_date} to {end_date}")
    logger.info("Note: Collection might take several hours due to API rate limits")

    current_date = start_date
    request_count = 0
    error_count = 0

    try:
        while current_date <= end_date:
            try:
                # Format current date
                current_date = format_timestamp(current_date)

                # Get odds data for current date
                odds_data = client.get_historical_odds(current_date)
                request_count += 1

                if not odds_data:
                    logger.warning(f"No odds data found for {current_date}")
                    # If no data, move forward by 1 hour to avoid getting stuck
                    current_date = (
                        datetime.fromisoformat(current_date.replace("Z", "+00:00"))
                        + timedelta(hours=1)
                    ).strftime("%Y-%m-%dT%H:%M:%SZ")
                    continue

                # Store the data
                with Session(client.engine) as session:
                    client.store_odds_snapshot(odds_data, session)

                logger.info(
                    f"Processed snapshot from {odds_data['timestamp']} "
                    f"({len(odds_data.get('data', []))} games)"
                )

                # Move to next snapshot using the next_timestamp from the response
                current_date = odds_data.get("next_timestamp")
                if not current_date or current_date > end_date:
                    break

                # Respect API rate limits (120 requests per minute)
                if request_count % 100 == 0:
                    logger.info("Pausing for rate limit...")
                    time.sleep(60)  # Wait 1 minute every 100 requests

            except Exception as e:
                error_count += 1
                logger.error(f"Error processing date {current_date}: {e}")

                if error_count >= 5:
                    logger.error("Too many consecutive errors, stopping collection")
                    break

                # Wait before retrying
                time.sleep(10)
                continue

    except KeyboardInterrupt:
        logger.info("\nCollection interrupted by user")
        logger.info(f"Last processed date: {current_date}")
        return

    logger.info("Historical odds collection completed")
    logger.info(f"Processed {request_count} snapshots")
    logger.info(f"Encountered {error_count} errors")


if __name__ == "__main__":
    collect_historical_odds()
