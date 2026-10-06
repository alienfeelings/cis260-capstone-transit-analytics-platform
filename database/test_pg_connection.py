import os
from pathlib import Path

import psycopg
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parents[1]

load_dotenv(PROJECT_ROOT / ".env")

DB_HOST = os.getenv("POSTGRES_HOST")
DB_PORT = os.getenv("POSTGRES_PORT")
DB_NAME = os.getenv("POSTGRES_DB")
DB_USER = os.getenv("POSTGRES_USER")
DB_PASSWORD = os.getenv("POSTGRES_PASSWORD")

'''
# Diagnostic lines.
print("Host:", DB_HOST)
print("Port:", DB_PORT)
print("Database:", DB_NAME)
print("User:", DB_USER)
print("Password loaded:", DB_PASSWORD is not None)
print("Password length:", len(DB_PASSWORD) if DB_PASSWORD else 0)
'''

with psycopg.connect(
    host=DB_HOST,
    port=DB_PORT,
    dbname=DB_NAME,
    user=DB_USER,
    password=DB_PASSWORD
) as connection:

    with connection.cursor() as cursor:
        cursor.execute("SELECT current_database();")
        database_name = cursor.fetchone()
        print(f"Connected to database: {database_name[0]}")

'''    
print("Successfully connected to PostgreSQL!")
connection.close()
print("Connection closed")
'''