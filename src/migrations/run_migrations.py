import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv
from initial_schema import upgrade
from urllib.parse import quote_plus

# Load environment variables
load_dotenv()

# Database Configuration from individual parameters
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
DB_NAME = os.getenv("DB_NAME")

# Validate all required parameters are present
required_params = {
    "DB_USER": DB_USER,
    "DB_PASSWORD": DB_PASSWORD,
    "DB_HOST": DB_HOST,
    "DB_PORT": DB_PORT,
    "DB_NAME": DB_NAME,
}

missing_params = [k for k, v in required_params.items() if not v]
if missing_params:
    raise ValueError(
        f"Missing required database parameters: {', '.join(missing_params)}"
    )


def test_connection(engine):
    """Test the database connection"""
    try:
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            print("✅ Successfully connected to database")
            return True
    except Exception as e:
        print(f"❌ Failed to connect to database: {e}")
        return False


def get_connection_url():
    """Build the database connection URL from individual parameters"""
    # URL encode the password to handle special characters
    encoded_password = quote_plus(DB_PASSWORD)

    # Construct the connection URL with SSL mode
    return f"postgresql://{DB_USER}:{encoded_password}@{DB_HOST}:{DB_PORT}/{DB_NAME}?sslmode=require"


def run_migrations():
    """Run database migrations on Supabase database"""
    print("\n🔄 Initializing database migration...")
    print(f"🔑 Connecting to database: {DB_HOST}")

    try:
        # Create SQLAlchemy engine with Supabase connection
        connection_url = get_connection_url()
        engine = create_engine(
            connection_url,
            connect_args={
                "connect_timeout": 30,
                "application_name": "ai-sports-model-builder",
            },
        )

        # Test the connection first
        if not test_connection(engine):
            return

        print("\n📦 Running migrations...")

        # Run the initial schema migration
        upgrade(engine)
        print("✨ Migrations completed successfully!")

    except Exception as e:
        print(f"\n❌ Error during migration process: {e}")
        print("\nDebug information:")
        print(f"Host: {DB_HOST}")
        print(f"Port: {DB_PORT}")
        print(f"Database: {DB_NAME}")
        print(f"User: {DB_USER}")
        raise


if __name__ == "__main__":
    run_migrations()
