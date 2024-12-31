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


def check_join_conditions():
    """Check various join conditions between tables"""
    engine = get_db_connection()

    # Check games table
    print("\nGames table sample:")
    games_query = text(
        """
        SELECT id, home_team_id, away_team_id, commence_time
        FROM nba_game_lines.games
        LIMIT 5;
    """
    )
    print(pd.read_sql(games_query, engine))

    # Check clean_game_odds table
    print("\nClean Game Odds table sample:")
    odds_query = text(
        """
        SELECT id, home_team_id, away_team_id, commence_time, home_price, away_price, spread, total
        FROM nba_game_lines.clean_game_odds
        WHERE has_spread = true AND has_totals = true
        LIMIT 5;
    """
    )
    print(pd.read_sql(odds_query, engine))

    # Check join matches
    print("\nJoin condition checks:")
    join_checks = text(
        """
        SELECT
            (SELECT COUNT(*) FROM nba_game_lines.games) as total_games,
            (SELECT COUNT(*) FROM nba_game_lines.clean_game_odds) as total_odds,
            (SELECT COUNT(*) 
             FROM nba_game_lines.games g
             JOIN nba_game_lines.clean_game_odds cgo 
             ON g.id = cgo.id) as id_matches,
            (SELECT COUNT(*) 
             FROM nba_game_lines.games g
             JOIN nba_game_lines.clean_game_odds cgo 
             ON cgo.home_team_id = g.home_team_id 
             AND cgo.away_team_id = g.away_team_id) as team_matches,
            (SELECT COUNT(*) 
             FROM nba_game_lines.games g
             JOIN nba_game_lines.clean_game_odds cgo 
             ON cgo.home_team_id = g.home_team_id 
             AND cgo.away_team_id = g.away_team_id
             AND cgo.commence_time = g.commence_time) as full_matches,
            (SELECT COUNT(*) 
             FROM nba_game_lines.games g
             JOIN nba_game_lines.clean_game_odds cgo 
             ON cgo.home_team_id = g.home_team_id 
             AND cgo.away_team_id = g.away_team_id
             AND cgo.commence_time = g.commence_time
             WHERE cgo.odds_timestamp <= g.commence_time
             AND cgo.has_spread = true
             AND cgo.has_totals = true) as valid_matches;
    """
    )
    print(pd.read_sql(join_checks, engine))

    # Check specific example of non-matching records
    print("\nExample of non-matching records:")
    mismatch_query = text(
        """
        SELECT g.id as game_id, g.home_team_id, g.away_team_id, g.commence_time,
               cgo.id as odds_id, cgo.home_team_id, cgo.away_team_id, cgo.commence_time
        FROM nba_game_lines.games g
        LEFT JOIN nba_game_lines.clean_game_odds cgo 
        ON cgo.home_team_id = g.home_team_id 
        AND cgo.away_team_id = g.away_team_id
        AND cgo.commence_time = g.commence_time
        WHERE cgo.id IS NULL
        LIMIT 5;
    """
    )
    print(pd.read_sql(mismatch_query, engine))


if __name__ == "__main__":
    check_join_conditions()
