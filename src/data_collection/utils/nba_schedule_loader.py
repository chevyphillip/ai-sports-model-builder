"""Load NBA schedule data into the database."""

import os
from typing import Dict, List
import psycopg2
from psycopg2.extras import execute_values
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class NBAScheduleLoader:
    """Load NBA schedule data into the database."""

    def __init__(self):
        """Initialize the loader with database connection details."""
        self.db_config = {
            "dbname": os.getenv("DB_NAME"),
            "user": os.getenv("DB_USER"),
            "password": os.getenv("DB_PASSWORD"),
            "host": os.getenv("DB_HOST"),
            "port": os.getenv("DB_PORT"),
            "sslmode": "require",  # Force SSL connection
        }

    def load_games(self, records: List[Dict]) -> int:
        """Load game records into the database.

        Args:
            records: List of game records to insert

        Returns:
            Number of records inserted/updated
        """
        if not records:
            print("No records to insert")
            return 0

        # SQL for upserting games
        upsert_sql = """
            INSERT INTO nba_game_lines.games (
                game_id,
                game_date,
                season_year,
                season,
                visitor_team,
                visitor_points,
                home_team,
                home_points,
                overtime,
                ot_periods,
                attendance,
                arena,
                source,
                scraped_at
            )
            VALUES %s
            ON CONFLICT (game_id) DO UPDATE SET
                visitor_points = EXCLUDED.visitor_points,
                home_points = EXCLUDED.home_points,
                overtime = EXCLUDED.overtime,
                ot_periods = EXCLUDED.ot_periods,
                attendance = EXCLUDED.attendance,
                arena = EXCLUDED.arena,
                source = EXCLUDED.source,
                scraped_at = EXCLUDED.scraped_at,
                updated_at = CURRENT_TIMESTAMP
            RETURNING 
                game_id,
                CASE 
                    WHEN xmax::text::int > 0 THEN 'UPDATE'
                    ELSE 'INSERT'
                END AS operation;
        """

        try:
            # Connect to the database
            with psycopg2.connect(**self.db_config) as conn:
                with conn.cursor() as cur:
                    # Convert records to list of tuples in the correct order
                    values = [
                        (
                            r["game_id"],
                            r["game_date"],
                            r["season_year"],
                            r["season"],
                            r["visitor_team"],
                            r["visitor_points"],
                            r["home_team"],
                            r["home_points"],
                            r.get("overtime", False),
                            r.get("ot_periods", 0),
                            r["attendance"],
                            r["arena"],
                            r["source"],
                            r["scraped_at"],
                        )
                        for r in records
                    ]

                    # Execute the upsert
                    result = execute_values(cur, upsert_sql, values, fetch=True)

                    # Count inserts and updates
                    inserts = sum(1 for r in result if r[1] == "INSERT")
                    updates = sum(1 for r in result if r[1] == "UPDATE")

                    print(f"Inserted {inserts} new games")
                    print(f"Updated {updates} existing games")

                    return len(result)

        except Exception as e:
            print(f"Error loading games into database: {e}")
            return 0
