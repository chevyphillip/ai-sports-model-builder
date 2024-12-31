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


def check_table_data(engine, table_name):
    """Check data in a specific table"""
    print(f"\nChecking {table_name} table:")

    try:
        # Get row count
        with engine.connect() as conn:
            count_query = text(f"SELECT COUNT(*) FROM nba_game_lines.{table_name}")
            count = conn.execute(count_query).scalar()
            print(f"Total rows: {count}")

            if count > 0:
                # Get sample data
                sample_query = text(
                    f"SELECT * FROM nba_game_lines.{table_name} LIMIT 5"
                )
                sample_df = pd.read_sql(sample_query, engine)
                print("\nSample data:")
                print(sample_df)

                # Get column info
                print("\nColumns:")
                for col in sample_df.columns:
                    print(f"- {col}: {sample_df[col].dtype}")
    except Exception as e:
        print(f"Error checking {table_name}: {e}")


def main():
    engine = get_db_connection()

    # Check each table
    tables = ["games", "nba_teams", "clean_game_odds", "game_odds"]
    for table in tables:
        check_table_data(engine, table)

    # Check join between tables
    print("\nChecking join between games, teams, and odds:")
    join_query = text(
        """
        SELECT 
            g.id as game_id,
            g.commence_time,
            ht.name as home_team,
            at.name as away_team,
            cgo.home_price,
            cgo.away_price,
            cgo.spread,
            cgo.total
        FROM nba_game_lines.games g
        JOIN nba_game_lines.nba_teams ht ON g.home_team_id = ht.id
        JOIN nba_game_lines.nba_teams at ON g.away_team_id = at.id
        LEFT JOIN nba_game_lines.clean_game_odds cgo ON g.id = cgo.id
        WHERE cgo.home_price IS NOT NULL
        AND cgo.away_price IS NOT NULL
        AND cgo.spread IS NOT NULL
        AND cgo.total IS NOT NULL
        LIMIT 5
    """
    )

    try:
        join_df = pd.read_sql(join_query, engine)
        print("\nSample joined data:")
        print(join_df)
    except Exception as e:
        print(f"Error checking join: {e}")


if __name__ == "__main__":
    main()
