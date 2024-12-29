"""Test script for basketball reference scraper."""

import logging
from datetime import datetime

import pandas as pd

from src.data_collection.basketball_reference_scraper import BasketballReferenceScraper
from src.models.game import Game
from src.utils.database import get_db_session, init_db

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def transform_to_game_model(row: pd.Series) -> Game:
    """Transform a pandas Series into a Game model."""
    # Extract points from separate visitor and home points columns
    visitor_points = int(row["Visitor PTS"])
    home_points = int(row["Home PTS"])

    # Calculate game metrics
    total_score = visitor_points + home_points
    score_difference = abs(visitor_points - home_points)
    home_win = home_points > visitor_points

    # Handle overtime
    overtime = False
    ot_periods = 0
    if "overtime" in row and pd.notna(row["overtime"]):
        overtime = True
        # Extract number of OT periods (e.g., "OT" -> 1, "2OT" -> 2)
        ot_str = str(row["overtime"])
        ot_periods = int(ot_str[0]) if len(ot_str) > 2 else 1

    return Game(
        game_id=row["game_id"],
        season=f"{row['season_year']}-{str(row['season_year'] + 1)[-2:]}",  # e.g., "2023-24"
        season_year=row["season_year"],
        game_date=row["Date"],
        game_day=str(row["game_day"]),
        game_month=row["game_month"],
        game_year=row["game_year"],
        day_of_week=row["day_of_week"],
        start_time="20:00",  # Default since not provided in data
        visitor_team_name=row["Visitor/Neutral"],
        home_team_name=row["Home/Neutral"],
        visitor_points=visitor_points,
        home_points=home_points,
        total_score=total_score,
        score_difference=score_difference,
        home_win=home_win,
        overtime=overtime,
        ot_periods=ot_periods,
        attendance=None,  # Not provided in this data source
        arena=None,  # Not provided in this data source
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )


def test_scraper():
    """Test the basketball reference scraper."""
    # Initialize scraper
    scraper = BasketballReferenceScraper()

    # Test scraping one month first
    logger.info("Testing single month scrape...")
    df = scraper.scrape_month(2012, "december")
    if df is not None:
        logger.info(f"Successfully scraped {len(df)} games")
        logger.info("\nDataFrame columns:")
        logger.info(df.columns.tolist())
        logger.info("\nFirst row:")
        logger.info(df.iloc[0].to_dict())

        # Transform first game to test data model
        if not df.empty:
            first_game = transform_to_game_model(df.iloc[0])
            logger.info(f"\nFirst game: {first_game.game_id}")
            logger.info(
                f"Teams: {first_game.visitor_team_name} @ {first_game.home_team_name}"
            )
            logger.info(f"Score: {first_game.visitor_points}-{first_game.home_points}")

            # Try inserting into database
            init_db()
            with get_db_session() as session:
                session.add(first_game)
                session.commit()
                logger.info("Successfully inserted game into database")


if __name__ == "__main__":
    test_scraper()
