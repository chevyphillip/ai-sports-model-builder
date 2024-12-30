"""Test NBA data scraping using FireCrawl client."""

import logging
from datetime import datetime

from sqlalchemy.exc import IntegrityError
from src.data_collection.firecrawl_client import FireCrawlClient
from src.models.game import Game
from src.utils.database import get_db_session, init_db

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def format_time(time_str: str) -> str:
    """Format time string to HH:MM format."""
    # Convert 12-hour format to 24-hour format
    if not time_str:
        return "00:00"

    # Remove any spaces
    time_str = time_str.strip()

    # Handle special cases
    if time_str == "Noon":
        return "12:00"

    # Extract hours, minutes, and period
    if "p" in time_str.lower():
        is_pm = True
        time_str = time_str.lower().replace("p", "")
    else:
        is_pm = False
        time_str = time_str.lower().replace("a", "")

    # Split hours and minutes
    if ":" in time_str:
        hours, minutes = map(int, time_str.split(":"))
    else:
        hours = int(time_str)
        minutes = 0

    # Convert to 24-hour format
    if is_pm and hours != 12:
        hours += 12
    elif not is_pm and hours == 12:
        hours = 0

    return f"{hours:02d}:{minutes:02d}"


def transform_to_game_model(game_data: dict) -> Game:
    """Transform scraped game data into a Game model."""
    # Parse date
    game_date = datetime.fromisoformat(game_data["date"])

    return Game(
        game_id=f"{game_date.strftime('%Y%m%d')}0{game_data['home_team'][-3:].upper()}",
        season=f"{game_date.year-1}-{str(game_date.year)[2:]}",  # e.g., "2023-24"
        season_year=game_date.year
        - 1,  # Use previous year for season (e.g., 2023 for 2023-24)
        game_date=game_date,
        game_day=str(game_date.day),
        game_month=game_date.month,
        game_year=game_date.year,
        day_of_week=game_date.strftime("%A"),
        start_time=format_time(game_data["start_time"]),
        visitor_team_name=game_data["visitor_team"],
        home_team_name=game_data["home_team"],
        visitor_points=game_data["visitor_points"],
        home_points=game_data["home_points"],
        total_score=game_data["visitor_points"] + game_data["home_points"],
        score_difference=abs(game_data["visitor_points"] - game_data["home_points"]),
        home_win=game_data["home_points"] > game_data["visitor_points"],
        overtime=False,  # We'll need to add this to the scraping
        ot_periods=0,  # We'll need to add this to the scraping
        attendance=game_data.get("attendance"),
        arena=game_data.get("arena"),
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )


def test_nba_scraping():
    """Test NBA schedule scraping and data insertion."""
    # Initialize the client
    client = FireCrawlClient()

    # Test scraping December 2012 data
    logger.info("Scraping December 2012 schedule data...")
    result = client.scrape_nba_schedule(2012, "december", use_local=False)

    if not result or not result.get("games"):
        logger.error("No games found in scraped data")
        return

    logger.info(f"Successfully scraped {len(result['games'])} games")

    # Initialize database
    init_db()

    # Transform and insert games
    with get_db_session() as session:
        games_added = 0
        games_skipped = 0

        for game_data in result["games"]:
            try:
                # Transform game data
                game = transform_to_game_model(game_data)

                # Try to add and commit each game individually
                session.add(game)
                session.commit()

                logger.info(
                    f"Added new game: {game.visitor_team_name} @ {game.home_team_name} "
                    f"({game.visitor_points}-{game.home_points})"
                )
                games_added += 1

            except IntegrityError:
                # Roll back the failed transaction
                session.rollback()
                logger.info(
                    f"Skipping duplicate game: {game.visitor_team_name} @ {game.home_team_name} "
                    f"({game.visitor_points}-{game.home_points})"
                )
                games_skipped += 1
                continue
            except Exception as e:
                # Roll back the failed transaction
                session.rollback()
                logger.error(f"Error processing game: {e}")
                continue

        logger.info(
            f"Successfully processed all games: {games_added} added, {games_skipped} skipped"
        )


if __name__ == "__main__":
    test_nba_scraping()
