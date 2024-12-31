import os
from dotenv import load_dotenv
import pandas as pd
from sqlalchemy import create_engine, text
from urllib.parse import quote_plus


def get_db_connection():
    """Create database connection"""
    load_dotenv()

    DB_USER = os.getenv("SUPABASE_DB_USER")
    DB_PASSWORD = quote_plus(os.getenv("SUPABASE_DB_PASSWORD"))
    DB_HOST = os.getenv("SUPABASE_DB_HOST")
    DB_PORT = os.getenv("SUPABASE_DB_PORT")
    DB_NAME = os.getenv("SUPABASE_DB_NAME")

    DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    return create_engine(DATABASE_URL)


def check_clean_game_odds():
    """Check the clean_game_odds table structure and data"""
    engine = get_db_connection()

    # Check table structure
    print("\nTable Structure:")
    structure_query = text(
        """
        SELECT column_name, data_type, is_nullable
        FROM information_schema.columns
        WHERE table_schema = 'nba_game_lines'
        AND table_name = 'clean_game_odds'
        ORDER BY ordinal_position;
    """
    )

    structure_df = pd.read_sql(structure_query, engine)
    print(structure_df)

    # Check data sample
    print("\nData Sample:")
    sample_query = text(
        """
        SELECT *
        FROM nba_game_lines.clean_game_odds
        LIMIT 5;
    """
    )

    sample_df = pd.read_sql(sample_query, engine)
    print(sample_df)

    # Check for empty or NULL values
    print("\nEmpty/NULL Value Counts:")
    null_query = text(
        """
        SELECT
            COUNT(*) as total_rows,
            COUNT(*) FILTER (WHERE home_price IS NULL) as null_home_price,
            COUNT(*) FILTER (WHERE away_price IS NULL) as null_away_price,
            COUNT(*) FILTER (WHERE spread IS NULL OR spread = '') as empty_spread,
            COUNT(*) FILTER (WHERE total IS NULL OR total = '') as empty_total,
            COUNT(*) FILTER (WHERE spread ~ '^[-]?[0-9]+[.]?[0-9]*$') as valid_spread,
            COUNT(*) FILTER (WHERE total ~ '^[-]?[0-9]+[.]?[0-9]*$') as valid_total
        FROM nba_game_lines.clean_game_odds;
    """
    )

    null_df = pd.read_sql(null_query, engine)
    print(null_df)

    # Check join conditions
    print("\nJoin Test:")
    join_query = text(
        """
        SELECT COUNT(*)
        FROM nba_game_lines.games g
        JOIN nba_game_lines.clean_game_odds cgo 
        ON cgo.home_team_id = g.home_team_id 
        AND cgo.away_team_id = g.away_team_id
        AND cgo.commence_time = g.commence_time
        WHERE cgo.odds_timestamp <= g.commence_time;
    """
    )

    join_count = engine.connect().execute(join_query).scalar()
    print(f"Matching rows in join: {join_count}")


if __name__ == "__main__":
    check_clean_game_odds()
