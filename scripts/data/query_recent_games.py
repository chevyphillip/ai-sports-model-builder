import os
from pathlib import Path
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from urllib.parse import quote_plus

# Load environment variables
env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=env_path, override=True)

# Schema name for NBA game line model
SCHEMA_NAME = "nba_game_lines"


def query_recent_games():
    """Query the most recent completed games from 2024"""
    # Create engine with properly escaped password
    url = f"postgresql://{os.getenv('DB_USER')}:{quote_plus(os.getenv('DB_PASSWORD'))}@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"
    engine = create_engine(url, echo=True, connect_args={"sslmode": "require"})

    # Query to get the most recent completed games from 2024
    query = text(
        f"""
        SELECT 
            game_date,
            visitor_team,
            visitor_points,
            home_team,
            home_points,
            arena
        FROM {SCHEMA_NAME}.games
        WHERE EXTRACT(YEAR FROM game_date) = 2024
        AND visitor_points > 0 
        AND home_points > 0
        ORDER BY game_date DESC
        LIMIT 10
    """
    )

    # Execute query and print results
    with engine.connect() as conn:
        result = conn.execute(query)
        print("\nMost recent completed games from 2024:")
        print("=" * 80)
        for row in result:
            print(f"Date: {row.game_date.strftime('%Y-%m-%d')}")
            print(
                f"{row.visitor_team} {row.visitor_points} @ {row.home_team} {row.home_points}"
            )
            print(f"Arena: {row.arena}")
            print("-" * 80)


if __name__ == "__main__":
    query_recent_games()
