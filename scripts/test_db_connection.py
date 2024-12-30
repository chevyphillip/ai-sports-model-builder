"""Test database connection."""

import os
from dotenv import load_dotenv
import psycopg2

# Load environment variables
load_dotenv()

# Database connection parameters
db_params = {
    "dbname": os.getenv("DB_NAME"),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD"),
    "host": os.getenv("DB_HOST"),
    "port": os.getenv("DB_PORT"),
    "sslmode": "require",
}

print("Connection parameters (excluding password):")
safe_params = {k: v for k, v in db_params.items() if k != "password"}
print(safe_params)

try:
    # Connect to the database
    print("\nConnecting to the database...")
    conn = psycopg2.connect(**db_params)
    print("Connected successfully!")

    # Create a cursor
    cur = conn.cursor()

    # Get server version
    cur.execute("SELECT version();")
    version = cur.fetchone()
    print(f"\nServer version:\n{version[0]}")

    # List available schemas
    cur.execute("SELECT schema_name FROM information_schema.schemata;")
    schemas = cur.fetchall()
    print("\nAvailable schemas:")
    for schema in schemas:
        print(f"- {schema[0]}")

    # Set search path to nba_game_lines schema
    if schema := os.getenv("DB_SCHEMA"):
        cur.execute(f"SET search_path TO {schema};")
        print(f"\nSet search path to: {schema}")

        # List tables in schema
        cur.execute(
            """
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = %s;
            """,
            (schema,),
        )
        tables = cur.fetchall()
        print(f"\nTables in {schema} schema:")
        for table in tables:
            print(f"- {table[0]}")

    # Close cursor and connection
    cur.close()
    conn.close()
    print("\nConnection closed.")

except Exception as e:
    print(f"Error: {e}")
