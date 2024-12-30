import psycopg2
from dotenv import load_dotenv
import os
from pathlib import Path

# Project root directory
PROJECT_ROOT = "/Users/chevyp/Development/ai-sports-model-builder"


def test_db_connection():
    # Get paths
    env_path = Path(PROJECT_ROOT) / ".env"
    cert_path = Path(PROJECT_ROOT) / "prod-ca-2021.crt"

    print(f"\nEnvironment file: {env_path}")
    print(f"SSL Certificate: {cert_path}")
    print(f"Files exist: env={env_path.exists()}, cert={cert_path.exists()}")

    # Load environment variables
    load_dotenv(dotenv_path=env_path)

    # Get connection parameters
    params = {
        "user": os.getenv("DB_USER"),
        "password": os.getenv("DB_PASSWORD"),
        "host": os.getenv("DB_HOST"),
        "port": os.getenv("DB_PORT", "5432"),
        "dbname": os.getenv("DB_NAME", "postgres"),
        "sslmode": "verify-full",
        "sslcert": str(cert_path),
    }

    print("\nConnection Parameters (excluding password):")
    for key, value in params.items():
        if key != "password":
            print(f"{key}: {value}")

    print("\nEnvironment variables (excluding password):")
    for key in os.environ:
        if key.startswith("DB_") and key != "DB_PASSWORD":
            print(f"{key}: {os.getenv(key)}")

    try:
        print("\nAttempting connection...")
        connection = psycopg2.connect(**params)
        print("✅ Connection successful!")

        # Test query
        with connection.cursor() as cursor:
            cursor.execute("SELECT NOW();")
            result = cursor.fetchone()
            print(f"Database time: {result[0]}")

        connection.close()
        print("Connection closed.")
        return True

    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return False


if __name__ == "__main__":
    test_db_connection()
