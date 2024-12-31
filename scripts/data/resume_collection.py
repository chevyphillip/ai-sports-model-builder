import logging
import os
from datetime import datetime

from src.data_collection.firecrawl_client import FireCrawlClient

# Configure logging
if not os.path.exists("logs"):
    os.makedirs("logs")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)

# Define months for NBA season
MONTHS = [
    "october",
    "november",
    "december",
]


def is_game_completed(game):
    """Check if a game has been completed by verifying scores are present."""
    return (
        game.get("visitor_points") is not None
        and game.get("home_points") is not None
        and game.get("visitor_points") != ""
        and game.get("home_points") != ""
    )


def process_and_insert_data(game_data):
    """Process and insert game data into the database."""
    client = FireCrawlClient()
    client.insert_game(game_data)


def resume_collection():
    logging.info("\nProcessing 2024-25 season games up to current date")

    # Initialize the client
    client = FireCrawlClient()

    # Process each month
    for month in MONTHS:
        logging.info(f"\nChecking {month.capitalize()} for 2024-25 season")

        try:
            # Use 2024 for current season games
            games = client.scrape_nba_schedule(2024, month)
            if not games:
                logging.info(f"No games found for {month.capitalize()}")
                continue

            if not isinstance(games, list):
                logging.error(f"Unexpected data format for {month.capitalize()}")
                continue

            # Filter out games that haven't been completed
            completed_games = [game for game in games if is_game_completed(game)]
            logging.info(
                f"Found {len(completed_games)} completed games for {month.capitalize()}"
            )

            # Log the last game details for verification
            if completed_games:
                last_game = completed_games[-1]
                logging.info("Last completed game details:")
                logging.info(f"Date: {last_game['game_date']}")
                logging.info(
                    f"Teams: {last_game['visitor_team']} ({last_game['visitor_points']}) @ {last_game['home_team']} ({last_game['home_points']})"
                )
                logging.info(f"Arena: {last_game['arena']}")

            # Process and insert each completed game
            for game in completed_games:
                try:
                    process_and_insert_data(game)
                    logging.info(
                        f"Successfully inserted/updated game {game['game_id']}"
                    )
                except Exception as e:
                    logging.error(
                        f"Error processing game {game.get('game_id', 'unknown')}: {str(e)}"
                    )

        except Exception as e:
            logging.error(f"Error processing {month}: {str(e)}")
            continue

    logging.info("\nCompleted processing 2024-25 season games")


if __name__ == "__main__":
    resume_collection()
