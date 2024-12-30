import os
from pathlib import Path
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from urllib.parse import quote_plus


def run_migrations():
    """Run all migrations in order"""
    # Load environment variables
    env_path = Path(__file__).resolve().parent.parent / ".env"
    load_dotenv(dotenv_path=env_path, override=True)

    # Create engine with SSL configuration and properly escaped password
    url = f"postgresql://{os.getenv('DB_USER')}:{quote_plus(os.getenv('DB_PASSWORD'))}@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"
    engine = create_engine(url, echo=True, connect_args={"sslmode": "require"})

    try:
        # Test connection
        with engine.connect() as conn:
            result = conn.execute(text("SELECT NOW();"))
            print(f"✅ Connected to database. Current time: {result.scalar()}")

        print("\nRunning migrations...")

        # Import and run migrations
        import importlib.util

        spec = importlib.util.spec_from_file_location(
            "initial_schema",
            os.path.join(os.path.dirname(__file__), "001_initial_schema.py"),
        )
        initial_schema = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(initial_schema)

        initial_schema.upgrade()

        print("\n✅ All migrations completed successfully!")

    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        raise


if __name__ == "__main__":
    run_migrations()
