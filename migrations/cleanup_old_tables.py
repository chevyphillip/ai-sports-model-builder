from sqlalchemy import create_engine, text
import os
from pathlib import Path
from dotenv import load_dotenv
from urllib.parse import quote_plus


def cleanup_old_tables():
    """Remove old tables from the public schema"""
    # Load environment variables
    env_path = Path(__file__).resolve().parent.parent / ".env"
    load_dotenv(dotenv_path=env_path, override=True)

    # Create engine with SSL configuration and properly escaped password
    url = f"postgresql://{os.getenv('DB_USER')}:{quote_plus(os.getenv('DB_PASSWORD'))}@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"
    engine = create_engine(url, echo=True, connect_args={"sslmode": "require"})

    # List of old tables to drop (in reverse order of dependencies)
    old_tables = ["model_performance", "predictions", "game_odds", "nba_games"]

    try:
        with engine.connect() as conn:
            # Check which tables exist
            existing_tables = []
            for table in old_tables:
                result = conn.execute(
                    text(
                        """
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables 
                        WHERE table_schema = 'public' 
                        AND table_name = :table_name
                    )
                    """
                    ),
                    {"table_name": table},
                )
                if result.scalar():
                    existing_tables.append(table)

            if not existing_tables:
                print("No old tables found in public schema.")
                return

            print(f"\nFound {len(existing_tables)} tables to remove:")
            for table in existing_tables:
                print(f"  - {table}")

            # Drop each table
            for table in existing_tables:
                conn.execute(text(f"DROP TABLE IF EXISTS public.{table} CASCADE"))
                print(f"✅ Dropped table: {table}")

            conn.commit()
            print("\n✅ Successfully cleaned up all old tables!")

    except Exception as e:
        print(f"\n❌ Cleanup failed: {e}")
        raise


if __name__ == "__main__":
    cleanup_old_tables()
