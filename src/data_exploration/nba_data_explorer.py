import os
from dotenv import load_dotenv
import pandas as pd
from sqlalchemy import create_engine, text
import seaborn as sns
import matplotlib.pyplot as plt
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


def connect_to_db():
    """Establish connection to the database"""
    try:
        engine = create_engine(DATABASE_URL)
        return engine
    except Exception as e:
        print(f"Error connecting to database: {e}")
        return None


def list_schema_tables(engine):
    """List all tables in the nba_game_lines schema"""
    try:
        with engine.connect() as conn:
            query = text(
                """
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'nba_game_lines'
                ORDER BY table_name
            """
            )
            result = conn.execute(query)
            return [row[0] for row in result]
    except Exception as e:
        print(f"Error listing tables: {e}")
        return []


def get_table_count(engine, table_name):
    """Get the number of rows in a table"""
    try:
        with engine.connect() as conn:
            result = conn.execute(
                text(f"SELECT COUNT(*) FROM nba_game_lines.{table_name}")
            )
            return result.scalar()
    except Exception as e:
        print(f"Error getting count for {table_name}: {e}")
        return 0


def get_table_columns(engine, table_name):
    """Get column information for a table"""
    try:
        with engine.connect() as conn:
            query = text(
                f"""
                SELECT column_name, data_type, is_nullable
                FROM information_schema.columns
                WHERE table_schema = 'nba_game_lines'
                AND table_name = '{table_name}'
                ORDER BY ordinal_position
            """
            )
            result = conn.execute(query)
            return [(row[0], row[1], row[2]) for row in result]
    except Exception as e:
        print(f"Error getting columns for {table_name}: {e}")
        return []


def get_table_sample(engine, table_name, limit=5):
    """Get a sample of rows from a table"""
    try:
        query = f"SELECT * FROM nba_game_lines.{table_name} LIMIT {limit}"
        return pd.read_sql(query, engine)
    except Exception as e:
        print(f"Error getting sample from {table_name}: {e}")
        return pd.DataFrame()


def get_date_range(engine, table_name, date_column):
    """Get the date range for a table with a date column"""
    try:
        with engine.connect() as conn:
            query = text(
                f"""
                SELECT 
                    MIN({date_column}) as earliest_date,
                    MAX({date_column}) as latest_date
                FROM nba_game_lines.{table_name}
            """
            )
            result = conn.execute(query)
            return result.fetchone()
    except Exception as e:
        print(f"Error getting date range for {table_name}: {e}")
        return None


def analyze_games_data(engine):
    """Analyze the games table data"""
    try:
        with engine.connect() as conn:
            # Get season distribution
            season_query = text(
                """
                SELECT season, COUNT(*) as games_count
                FROM nba_game_lines.games
                GROUP BY season
                ORDER BY season
            """
            )
            seasons_df = pd.read_sql(season_query, conn)
            print("\nGames per season:")
            print(seasons_df)

            # Get game status distribution
            status_query = text(
                """
                SELECT status, COUNT(*) as count
                FROM nba_game_lines.games
                GROUP BY status
            """
            )
            status_df = pd.read_sql(status_query, conn)
            print("\nGame status distribution:")
            print(status_df)

    except Exception as e:
        print(f"Error analyzing games data: {e}")


def analyze_odds_data(engine):
    """Analyze the betting odds data"""
    try:
        with engine.connect() as conn:
            # Get market type distribution
            market_query = text(
                """
                SELECT market_type, COUNT(*) as count
                FROM nba_game_lines.betting_odds
                GROUP BY market_type
            """
            )
            market_df = pd.read_sql(market_query, conn)
            print("\nBetting market type distribution:")
            print(market_df)

            # Get bookmaker distribution
            bookmaker_query = text(
                """
                SELECT bookmaker, COUNT(*) as count
                FROM nba_game_lines.betting_odds
                GROUP BY bookmaker
                ORDER BY count DESC
            """
            )
            bookmaker_df = pd.read_sql(bookmaker_query, conn)
            print("\nBookmaker distribution:")
            print(bookmaker_df)

    except Exception as e:
        print(f"Error analyzing odds data: {e}")


def main():
    """Main function to explore the database"""
    engine = connect_to_db()
    if not engine:
        return

    print("\nExploring NBA Game Lines Database:")
    print("\nAvailable tables in nba_game_lines schema:")
    tables = list_schema_tables(engine)

    for table in tables:
        print(f"\n{table.upper()} table:")

        # Get column information
        print("\nColumns:")
        columns = get_table_columns(engine, table)
        for col_name, data_type, nullable in columns:
            print(f"  - {col_name}: {data_type} (Nullable: {nullable})")

        # Get row count
        count = get_table_count(engine, table)
        print(f"\nTotal rows: {count}")

        if count > 0:
            print("\nSample data:")
            sample_df = get_table_sample(engine, table)
            print(sample_df)

            # Get date range for tables with date columns
            if table == "games":
                date_range = get_date_range(engine, table, "game_date")
                if date_range:
                    print(f"\nDate range: {date_range[0]} to {date_range[1]}")
                analyze_games_data(engine)

            elif table == "betting_odds":
                analyze_odds_data(engine)


if __name__ == "__main__":
    main()
