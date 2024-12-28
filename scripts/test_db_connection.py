"""Test Supabase database connection."""

import os
from pathlib import Path
import psycopg2
from psycopg2 import OperationalError


def load_env_file(env_path):
    """Load environment variables from file manually."""
    env_vars = {}
    with open(env_path) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#"):
                key, value = line.split("=", 1)
                env_vars[key.strip()] = value.strip()
    return env_vars


def test_connection():
    """Test connection to Supabase database."""
    # Get the project root directory and load environment
    project_root = Path(__file__).parent.parent
    env_path = project_root / ".env"

    print(f"Reading .env file from: {env_path}")
    env_vars = load_env_file(env_path)

    # Print loaded environment variables (excluding sensitive data)
    print("\nLoaded Environment Variables:")
    safe_vars = ["DB_HOST", "DB_PORT", "DB_NAME", "DB_USER", "DB_SCHEMA"]
    for var in safe_vars:
        print(f"{var}: {env_vars.get(var)}")

    try:
        # Attempt to establish a connection
        print("\nAttempting to connect to Supabase database...")
        conn = psycopg2.connect(
            dbname=env_vars.get("DB_NAME"),
            user=env_vars.get("DB_USER"),
            password=env_vars.get("DB_PASSWORD"),
            host=env_vars.get("DB_HOST"),
            port=int(env_vars.get("DB_PORT")),
            sslmode="require",
        )

        # Get server version
        cursor = conn.cursor()
        cursor.execute("SELECT version();")
        version = cursor.fetchone()
        print(f"Successfully connected to database!")
        print(f"Server version: {version[0]}")

        # Set and verify schema
        schema_name = env_vars.get("DB_SCHEMA")
        cursor.execute(f"SET search_path TO {schema_name};")
        cursor.execute("SELECT current_schema();")
        current_schema = cursor.fetchone()[0]
        print(f"Current schema: {current_schema}")

        # List available schemas
        cursor.execute(
            """
            SELECT schema_name 
            FROM information_schema.schemata 
            WHERE schema_name NOT IN ('information_schema', 'pg_catalog', 'pg_toast');
        """
        )
        schemas = cursor.fetchall()
        print("\nAvailable schemas:")
        for schema in schemas:
            print(f"- {schema[0]}")

        # Test query to list all tables in the schema
        cursor.execute(
            """
            SELECT 
                table_name,
                (SELECT count(*) FROM information_schema.columns 
                 WHERE table_schema = t.table_schema 
                 AND table_name = t.table_name) as column_count
            FROM information_schema.tables t
            WHERE table_schema = %s
            ORDER BY table_name;
            """,
            (schema_name,),
        )
        tables = cursor.fetchall()
        print(f"\nTables in schema '{schema_name}':")
        if tables:
            for table, column_count in tables:
                print(f"- {table} ({column_count} columns)")
        else:
            print("No tables found in the schema.")

        # For each table, get detailed column information
        if tables:
            print("\nDetailed Schema Information:")
            for table_name, _ in tables:
                cursor.execute(
                    """
                    SELECT 
                        column_name,
                        data_type,
                        is_nullable,
                        column_default,
                        character_maximum_length
                    FROM 
                        information_schema.columns
                    WHERE 
                        table_schema = %s
                        AND table_name = %s
                    ORDER BY 
                        ordinal_position;
                    """,
                    (schema_name, table_name),
                )
                columns = cursor.fetchall()
                print(f"\n{table_name}:")
                for col_name, data_type, nullable, default, max_length in columns:
                    nullable_str = "NULL" if nullable == "YES" else "NOT NULL"
                    default_str = f" DEFAULT {default}" if default else ""
                    length_str = f"({max_length})" if max_length else ""
                    print(
                        f"  - {col_name}: {data_type}{length_str} {nullable_str}{default_str}"
                    )

        cursor.close()
        conn.close()
        print("\nConnection test completed successfully!")
        return True

    except OperationalError as e:
        print(f"Error connecting to database: {e}")
        return False
    except Exception as e:
        print(f"Unexpected error: {e}")
        print(f"Error type: {type(e)}")
        return False


if __name__ == "__main__":
    test_connection()
