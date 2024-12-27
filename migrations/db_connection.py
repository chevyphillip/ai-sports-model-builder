import os
from pathlib import Path
from sqlalchemy import create_engine
from dotenv import load_dotenv
import psycopg2

# Project root directory
PROJECT_ROOT = "/Users/chevyp/Development/ai-sports-model-builder"


def test_direct_connection():
    """Test direct connection using psycopg2"""
    # Load environment variables
    env_path = Path(PROJECT_ROOT) / ".env"
    cert_path = Path(PROJECT_ROOT) / "prod-ca-2021.crt"

    print(f"\nTesting direct connection...")
    print(f"Using SSL certificate at: {cert_path}")
    print(f"Using .env file at: {env_path}")

    # Load environment variables
    load_dotenv(dotenv_path=env_path, override=True)

    try:
        connection = psycopg2.connect(
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD"),
            host=os.getenv("DB_HOST"),
            port=os.getenv("DB_PORT", "5432"),
            dbname=os.getenv("DB_NAME", "postgres"),
            sslmode="verify-full",
            sslcert=str(cert_path),
        )

        print("✅ Direct connection successful!")

        # Test query
        with connection.cursor() as cursor:
            cursor.execute("SELECT NOW();")
            result = cursor.fetchone()
            print(f"Database time: {result[0]}")

        connection.close()
        return True

    except Exception as e:
        print(f"❌ Direct connection failed: {e}")
        print("\nEnvironment variables (excluding password):")
        for key in os.environ:
            if key.startswith("DB_") and key != "DB_PASSWORD":
                print(f"{key}: {os.getenv(key)}")
        return False


def get_db_connection():
    """Get database connection with environment variables"""
    # First test direct connection
    if not test_direct_connection():
        raise ConnectionError("Failed to establish direct connection to database")

    # Load environment variables
    env_path = Path(PROJECT_ROOT) / ".env"
    cert_path = Path(PROJECT_ROOT) / "prod-ca-2021.crt"

    load_dotenv(dotenv_path=env_path, override=True)

    # Get database configuration
    config = {
        "user": os.getenv("DB_USER"),
        "password": os.getenv("DB_PASSWORD"),
        "host": os.getenv("DB_HOST"),
        "port": os.getenv("DB_PORT", "5432"),
        "database": os.getenv("DB_NAME", "postgres"),
    }

    # Print configuration (excluding password)
    print("\nDatabase Configuration:")
    for key, value in config.items():
        if key != "password":
            print(f"{key}: {value}")

    # Create connection URL
    url = f"postgresql://{config['user']}:{config['password']}@{config['host']}:{config['port']}/{config['database']}"

    # Create and return SQLAlchemy engine with SSL configuration
    return create_engine(
        url,
        echo=True,  # Show SQL queries
        pool_pre_ping=True,  # Check connection before using
        pool_size=5,
        max_overflow=10,
        connect_args={"sslmode": "verify-full", "sslcert": str(cert_path)},
    )
