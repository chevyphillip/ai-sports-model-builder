import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from urllib.parse import quote_plus


def init_database():
    """Initialize the database with the schema"""
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
        with open("src/database/init_schema.sql", "r") as file:
            schema_sql = file.read()

        # Execute the schema SQL
        with engine.connect() as conn:
            conn.execute(text(schema_sql))
            conn.commit()

        print("Database schema initialized successfully!")

        # Verify tables were created
        with engine.connect() as conn:
            result = conn.execute(
                text(
                    """
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
            """
                )
            )
            print("\nCreated tables:")
            for row in result:
                print(f"- {row[0]}")

    except Exception as e:
        print(f"Error initializing database: {e}")


if __name__ == "__main__":
    init_database()
