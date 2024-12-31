import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from urllib.parse import quote_plus


def create_game_results_table():
    """Create the game results table in the database"""
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

    try:
        # Create database engine
        engine = create_engine(DATABASE_URL)

        # Read the schema SQL file
        with open("src/database/game_results_schema.sql", "r") as file:
            schema_sql = file.read()

        # Execute the schema SQL
        with engine.connect() as conn:
            conn.execute(text(schema_sql))
            conn.commit()

        print("Game results table created successfully!")

        # Verify table was created
        with engine.connect() as conn:
            result = conn.execute(
                text(
                    """
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = 'nba_game_lines'
                    AND table_name = 'game_results'
                )
            """
                )
            )
            exists = result.scalar()

            if exists:
                print("Table verification successful!")
            else:
                print("Error: Table was not created!")

    except Exception as e:
        print(f"Error creating game results table: {e}")


if __name__ == "__main__":
    create_game_results_table()
