import logging
from datetime import datetime

from src.models.game import Game
from src.utils.database import get_db_session, init_db

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_game_insertion():
    """Test inserting a game into the database."""
    # Initialize the database
    init_db()

    # Create a sample game
    test_game = Game(
        game_id="202312280LAL",
        season="2023-24",
        season_year=2023,
        game_date=datetime(2023, 12, 28, 20, 0),  # 8:00 PM
        game_day="28",
        game_month=12,
        game_year=2023,
        day_of_week="Thursday",
        start_time="20:00",
        visitor_team_name="Charlotte Hornets",
        home_team_name="Los Angeles Lakers",
        visitor_points=115,
        home_points=126,
        total_score=241,
        score_difference=11,
        home_win=True,
        overtime=False,
        ot_periods=0,
        attendance=18997,
        arena="Crypto.com Arena",
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )

    # Insert the game into the database
    with get_db_session() as session:
        session.add(test_game)
        session.commit()
        logger.info(f"Successfully inserted game: {test_game.game_id}")

        # Retrieve the game from the database
        inserted_game = session.query(Game).filter_by(game_id=test_game.game_id).first()
        logger.info(f"Retrieved game from database: {inserted_game.game_id}")
        logger.info(f"Home team: {inserted_game.home_team_name}")
        logger.info(
            f"Score: {inserted_game.home_points} - {inserted_game.visitor_points}"
        )


if __name__ == "__main__":
    test_game_insertion()
