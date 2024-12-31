import logging
import os
from datetime import datetime
from typing import Dict, List, Optional
from src.data_collection.firecrawl_client import FireCrawlClient
from src.data_collection.nba_schedule_transformer import NBAScheduleTransformer
from src.data_collection.nba_schedule_loader import NBAScheduleLoader

# Create logs directory if it doesn't exist
os.makedirs("logs", exist_ok=True)

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(
            f'logs/nba_data_collection_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'
        ),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger(__name__)


class NBASeasonCollector:
    def __init__(self):
        self.client = FireCrawlClient()
        self.transformer = NBAScheduleTransformer()
        self.loader = NBAScheduleLoader()
        self.months = [
            "october",
            "november",
            "december",
            "january",
            "february",
            "march",
            "april",
            "may",
            "june",
        ]

    def collect_month(self, season_year: int, month: str) -> Optional[Dict]:
        """Collect data for a specific month and season."""
        try:
            logger.info(f"Collecting data for {month.capitalize()} {season_year}")
            data = self.client.scrape_nba_schedule(season_year, month, use_local=False)
            games = data.get("games", [])
            if games:
                logger.info(
                    f"Found {len(games)} games for {month.capitalize()} {season_year}"
                )
                return data
            logger.info(f"No games found for {month.capitalize()} {season_year}")
            return None
        except Exception as e:
            logger.error(
                f"Error collecting data for {month.capitalize()} {season_year}: {e}"
            )
            return None

    def process_and_insert_data(self, data: Dict) -> int:
        """Transform and insert data into the database."""
        try:
            # Transform data
            records = self.transformer.transform_to_dict_records(data)
            if not records:
                logger.warning("No records produced by transformer")
                return 0

            # Insert data
            num_loaded = self.loader.load_games(records)
            logger.info(f"Successfully loaded {num_loaded} games into database")
            return num_loaded
        except Exception as e:
            logger.error(f"Error processing and inserting data: {str(e)}")
            logger.error(f"Data sample: {str(data.get('games', [])[:1])}")
            return 0

    def collect_season(self, season_year: int) -> int:
        """Collect all available data for a specific season."""
        total_games = 0
        logger.info(f"Starting collection for {season_year-1}-{season_year} season")

        for month in self.months:
            data = self.collect_month(season_year, month)
            if data:
                games_loaded = self.process_and_insert_data(data)
                total_games += games_loaded

        logger.info(
            f"Completed {season_year-1}-{season_year} season. Total games: {total_games}"
        )
        return total_games


def main():
    """Main function to collect all NBA seasons from 2011 to 2024."""
    collector = NBASeasonCollector()
    total_games = 0

    logger.info("Starting collection of all NBA seasons from 2011 to 2024")

    for season_year in range(2011, 2025):
        try:
            season_games = collector.collect_season(season_year)
            total_games += season_games
            logger.info(
                f"Completed season {season_year}. Running total: {total_games} games"
            )
        except Exception as e:
            logger.error(f"Error processing season {season_year}: {e}")
            continue

    logger.info(f"Data collection completed. Total games collected: {total_games}")


if __name__ == "__main__":
    main()
