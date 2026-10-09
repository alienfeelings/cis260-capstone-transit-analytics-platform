import os
from pathlib import Path

import psycopg
from dotenv import load_dotenv

# Find the project root
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Load variables from .env
load_dotenv(PROJECT_ROOT / ".env")

# Find schema.sql
SCHEMA_FILE = Path(__file__).resolve().parent / "schema.sql"

DB_HOST = os.getenv("POSTGRES_HOST")
DB_PORT = os.getenv("POSTGRES_PORT")
DB_NAME = os.getenv("POSTGRES_DB")
DB_USER = os.getenv("POSTGRES_USER")
DB_PASSWORD = os.getenv("POSTGRES_PASSWORD")

def create_schema():
    connection = psycopg.connect(
        host=DB_HOST,
        port=DB_PORT,
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD
    )

    print("Connected to PostgreSQL.")

    try:
        with connection.cursor() as cursor:

            # Read the SQL schema file
            schema_sql = SCHEMA_FILE.read_text(encoding="utf-8")
#-------------
            print("Schema file:", SCHEMA_FILE)
            print("Schema file exists:", SCHEMA_FILE.exists())
            print("Schema file length:", len(schema_sql))
#--------------
            # Execute the schema
            cursor.execute(schema_sql)

        connection.commit()

        print("Schema SQL commited.")

        with connection.cursor() as cursor:

            # Verify the tables
            cursor.execute("""
                SELECT table_name
                FROM information_schema.tables
                WHERE table_schema = 'public'
                ORDER BY table_name;
            """)

            tables = cursor.fetchall()

            print("\nTables created:")

            for table in tables:
                print(table[0])

    except Exception:
        connection.rollback()
        print("\nSchema creation failed. Changed rolled back.")
        raise

    finally:
        connection.close()

if __name__ == "__main__":
    create_schema()

