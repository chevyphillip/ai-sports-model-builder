"""Test the NBA data pipeline from scraping to database insertion."""

import logging
import os
from datetime import datetime
from pathlib import Path

from sqlalchemy import text

from src.data_collection.firecrawl_client import FireCrawlClient
from src.models.game import Game
from src.models.team import Team, SportType
from src.utils.database import get_db_session, init_db
from scripts.transform_nba_data import transform_nba_data

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def ensure_teams_exist(session, game_data):
    """Ensure teams exist in the database."""
    teams_to_check = {
        game_data["visitor_team"]: game_data["visitor_team"].split()[-1],
        game_data["home_team"]: game_data["home_team"].split()[-1],
    }

    for full_name, nickname in teams_to_check.items():
        team = session.query(Team).filter_by(name=nickname, sport=SportType.NBA).first()

        if not team:
            city = " ".join(full_name.split()[:-1])
            team = Team(
                name=nickname,
                city=city,
                sport=SportType.NBA,
                abbreviation="TBD",  # You might want to add a mapping for this
                division="TBD",  # These could be added to the scraping
                conference="TBD",  # or maintained in a separate mapping
                venue="TBD",
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
            )
            session.add(team)
            logger.info(f"Created team: {full_name}")

    session.flush()


def insert_game_data(transformed_data):
    """Insert transformed game data into the database."""
    try:
        with get_db_session() as session:
            # Set schema explicitly for this session
            if schema := os.getenv("DB_SCHEMA"):
                session.execute(text(f"SET search_path TO {schema}"))

            # Process each game
            for game_data in transformed_data["games"]:
                # Ensure teams exist
                ensure_teams_exist(session, game_data)

                # Check if game already exists
                existing_game = (
                    session.query(Game).filter_by(game_id=game_data["game_id"]).first()
                )

                if existing_game:
                    logger.info(f"Game already exists: {game_data['game_id']}")
                    continue

                # Create new game
                game = Game(
                    game_id=game_data["game_id"],
                    season=game_data["season"],
                    season_year=game_data["season_year"],
                    game_date=datetime.fromisoformat(game_data["date"]),
                    game_day=game_data["game_day"],
                    game_month=game_data["game_month"],
                    game_year=game_data["game_year"],
                    day_of_week=game_data["day_of_week"],
                    start_time=game_data["start_time_24h"],
                    visitor_team_name=game_data["visitor_team"],
                    home_team_name=game_data["home_team"],
                    visitor_points=game_data["visitor_points"],
                    home_points=game_data["home_points"],
                    total_score=game_data["total_score"],
                    score_difference=game_data["score_difference"],
                    home_win=game_data["home_win"],
                    overtime=game_data["overtime"],
                    ot_periods=game_data["ot_periods"],
                    attendance=game_data["attendance"],
                    arena=game_data["arena"],
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow(),
                )
                session.add(game)
                logger.info(f"Inserted game: {game_data['game_id']}")

            session.commit()
            logger.info("Successfully inserted all games")

    except Exception as e:
        logger.error(f"Error inserting game data: {e}")
        raise


def test_nba_pipeline():
    """Test the entire NBA data pipeline."""
    try:
        # Initialize database
        init_db()

        # 1. Scrape data
        logger.info("Starting web scraping...")
        client = FireCrawlClient()
        scraped_data = client.scrape_nba_schedule(2024, "march", use_local=True)

        # Save scraped data
        data_dir = Path("data/raw/nba_schedules")
        data_dir.mkdir(parents=True, exist_ok=True)
        scrape_file = data_dir / "latest_scrape.json"
        client.save_schedule_data(scraped_data, 2024, str(data_dir))

        # 2. Transform data
        logger.info("Transforming data...")
        transformed_data = transform_nba_data(str(scrape_file))

        # 3. Insert into database
        logger.info("Inserting data into database...")
        insert_game_data(transformed_data)

        logger.info("Pipeline completed successfully!")

    except Exception as e:
        logger.error(f"Pipeline failed: {e}")
        raise


if __name__ == "__main__":
    test_nba_pipeline()
