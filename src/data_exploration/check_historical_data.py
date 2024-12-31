import os
from dotenv import load_dotenv
import pandas as pd
from sqlalchemy import create_engine, text
from urllib.parse import quote_plus

# Load environment variables
load_dotenv()

# Database connection parameters
DB_USER = os.getenv("SUPABASE_DB_USER")
DB_PASSWORD = quote_plus(os.getenv("SUPABASE_DB_PASSWORD"))
DB_HOST = os.getenv("SUPABASE_DB_HOST")
DB_PORT = os.getenv("SUPABASE_DB_PORT")
DB_NAME = os.getenv("SUPABASE_DB_NAME")

# Create database connection URL
DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"


def check_historical_data():
    """Check what historical game data we have in the database"""
    engine = create_engine(DATABASE_URL)

    try:
        # Check games table structure
        games_columns_query = """
        SELECT column_name, data_type 
        FROM information_schema.columns 
        WHERE table_schema = 'nba_game_lines' 
        AND table_name = 'games'
        ORDER BY ordinal_position;
        """

        games_columns_df = pd.read_sql(games_columns_query, engine)
        print("\nGames table structure:")
        print(games_columns_df)

        # Check clean_game_odds table structure
        clean_odds_columns_query = """
        SELECT column_name, data_type 
        FROM information_schema.columns 
        WHERE table_schema = 'nba_game_lines' 
        AND table_name = 'clean_game_odds'
        ORDER BY ordinal_position;
        """

        clean_odds_columns_df = pd.read_sql(clean_odds_columns_query, engine)
        print("\nClean Game Odds table structure:")
        print(clean_odds_columns_df)

        # Get sample of completed games
        completed_games_query = """
        SELECT 
            g.id,
            g.game_id,
            g.commence_time,
            ht.name as home_team,
            at.name as away_team,
            cgo.*
        FROM nba_game_lines.games g
        JOIN nba_game_lines.nba_teams ht ON g.home_team_id = ht.id
        JOIN nba_game_lines.nba_teams at ON g.away_team_id = at.id
        JOIN nba_game_lines.clean_game_odds cgo ON g.id = cgo.id
        WHERE g.commence_time < CURRENT_TIMESTAMP
        ORDER BY g.commence_time DESC
        LIMIT 5;
        """

        completed_games_df = pd.read_sql(completed_games_query, engine)
        print("\nSample of completed games:")
        print(completed_games_df)

        # Get date range of completed games
        completed_range_query = """
        SELECT 
            MIN(g.commence_time) as earliest_completed,
            MAX(g.commence_time) as latest_completed,
            COUNT(*) as total_completed
        FROM nba_game_lines.games g
        WHERE g.commence_time < CURRENT_TIMESTAMP;
        """

        completed_range_df = pd.read_sql(completed_range_query, engine)
        print("\nCompleted games date range:")
        print(completed_range_df)

    except Exception as e:
        print(f"Error checking historical data: {e}")


if __name__ == "__main__":
    check_historical_data()
