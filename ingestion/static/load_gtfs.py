import os
import csv
from idlelib.iomenu import encoding
from os import read
from pathlib import Path

import psycopg
from dotenv import load_dotenv

from database.test_pg_connection import DB_HOST

# ============================================================
# PROJECT PATHS
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[2]

load_dotenv(PROJECT_ROOT / ".env")

GTFS_DIR = PROJECT_ROOT / "data" / "gtfs"

# ============================================================
# DATABASE SETTINGS
# ============================================================

DB_HOST = os.getenv("POSTGRES_HOST")
DB_PORT = os.getenv("POSTGRES_PORT")
DB_NAME = os.getenv("POSTGRES_DB")
DB_USER = os.getenv("POSTGRES_USER")
DB_PASSWORD = os.getenv("POSTGRES_PASSWORD")

# ============================================================
# CLEANING FUNCTIONS
# ============================================================

def clean_text(value):
    if value is None or value == "":
        return None
    return value

def clean_int(value):
    if value is None or value == "":
        return None
    return int(value)

def clean_float(value):
    if value is None or value == "":
        return None
    return float(value)

# ============================================================
# LOAD ROUTES
# ============================================================

def load_routes(cursor):
    file_path = GTFS_DIR / "routes.txt"

    print("\nLoading routes...")

    with file_path.open(
        mode="r",
        encoding="utf-8-sig",
        newline=""
    ) as file:
        reader = csv.DictReader(file)

        with cursor.copy("""
            COPY routes (
                route_id,
                agency_id,
                route_short_name,
                route_long_name,
                route_desc,
                route_type,
                route_url,
                route_color,
                route_text_color,
                route_sort_order
            )
            FROM STDIN
        """) as copy:

            count = 0
            for row in reader:
                copy.write_row([
                    clean_text(row.get("route_id")),
                    clean_text(row.get("agency_id")),
                    clean_text(row.get("route_short_name")),
                    clean_text(row.get("route_long_name")),
                    clean_text(row.get("route_desc")),
                    clean_int(row.get("route_type")),
                    clean_text(row.get("route_url")),
                    clean_text(row.get("route_color")),
                    clean_text(row.get("route_text_color")),
                    clean_int(row.get("route_sort_order"))
                ])
                count += 1
    print(f"Loaded {count:,} routes.")

# ============================================================
# LOAD STOPS
# ============================================================

def load_stops(cursor):
    file_path = GTFS_DIR / "stops.txt"

    print("\nLoading stops...")

    with file_path.open(
        mode="r",
        encoding="utf-8-sig",
        newline=""
    ) as file:

        reader = csv.DictReader(file)

        with cursor.copy("""
            COPY stops (
                stop_id,
                stop_code,
                stop_name,
                stop_desc,
                platform_code,
                platform_name,
                stop_lat,
                stop_lon,
                zone_id,
                stop_address,
                stop_url,
                location_type,
                parent_station,
                wheelchair_boarding
            )
            FROM STDIN
        """) as copy:

            count = 0
            for row in reader:
                copy.write_row([
                    clean_text(row.get("stop_id")),
                    clean_text(row.get("stop_code")),
                    clean_text(row.get("stop_name")),
                    clean_text(row.get("stop_desc")),
                    clean_text(row.get("platform_code")),
                    clean_text(row.get("platform_name")),
                    clean_float(row.get("stop_lat")),
                    clean_float(row.get("stop_lon")),
                    clean_text(row.get("zone_id")),
                    clean_text(row.get("stop_address")),
                    clean_text(row.get("stop_url")),
                    clean_int(row.get("location_type")),
                    clean_text(row.get("parent_station")),
                    clean_int(row.get("wheelchair_boarding"))
                ])
                count += 1

    print(f"Loaded {count:,} stops.")

# ============================================================
# LOAD TRIPS
# ============================================================

def load_trips(cursor):
    file_path = GTFS_DIR / "trips.txt"

    print("\nLoading trips...")

    with file_path.open(
        mode="r",
        encoding="utf-8-sig",
        newline=""
    ) as file:
         reader = csv.DictReader(file)

         with cursor.copy("""
             COPY trips (
                 trip_id,
                 route_id,
                 service_id,
                 trip_headsign,
                 trip_short_name,
                 direction_id,
                 block_id,
                 shape_id,
                 wheelchair_accessible
             )
             FROM STDIN
         """) as copy:

             count = 0
             for row in reader:
                 copy.write_row([
                     clean_text(row.get("trip_id")),
                     clean_text(row.get("route_id")),
                     clean_text(row.get("service_id")),
                     clean_text(row.get("trip_headsign")),
                     clean_text(row.get("trip_short_name")),
                     clean_int(row.get("direction_id")),
                     clean_text(row.get("block_id")),
                     clean_text(row.get("shape_id")),
                     clean_int(row.get("wheelchair_accessible"))
                 ])
                 count += 1
    print(f"Loaded {count:,} trips.")

# ============================================================
# LOAD STOP TIMES
# ============================================================

def load_stop_times(cursor):
    file_path = GTFS_DIR / "stop_times.txt"

    print("\nLoading stop times...")

    with file_path.open(
        mode="r",
        encoding="utf-8-sig",
        newline=""
    ) as file:

        reader = csv.DictReader(file)

        with cursor.copy("""
            COPY stop_times (
                trip_id,
                arrival_time,
                departure_time,
                stop_id,
                stop_sequence,
                stop_headsign,
                pickup_type,
                drop_off_type,
                timepoint
            )
            FROM STDIN
        """) as copy:

            count = 0
            for row in reader:
                copy.write_row([
                    clean_text(row.get("trip_id")),
                    clean_text(row.get("arrival_time")),
                    clean_text(row.get("departure_time")),
                    clean_text(row.get("stop_id")),
                    clean_int(row.get("stop_sequence")),
                    clean_text(row.get("stop_headsign")),
                    clean_int(row.get("pickup_type")),
                    clean_int(row.get("drop_off_type")),
                    clean_int(row.get("timepoint"))
                ])
                count += 1
    # We use .get() to intentionally extract only the columns we need.
    print(f"Loaded {count:,} stop times.")

# ============================================================
# MAIN GTFS LOAD
# ============================================================

def load_gtfs():
    print("Connecting to PostgreSQL...")

    connection = psycopg.connect(
        host=DB_HOST,
        port=DB_PORT,
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD
    )
    print("Connected.")

    #temporary
    # with connection.cursor() as cursor:
    #     cursor.execute("""
    #         SELECT current_database(), current_schema();
    #     """)
    #
    #     database_name, schema_name = cursor.fetchone()
    #
    #     print("Database:", database_name)
    #     print("Schema:", schema_name)
    #
    #     cursor.execute("""
    #         SELECT table_name
    #         FROM information_schema.tables
    #         WHERE table_schema = 'public'
    #         ORDER BY table_name;
    #     """)
    #
    #     tables = cursor.fetchall()
    #
    #     print("\nTables found:")
    #
    #     for table in tables:
    #         print(table[0])
#temporary

    try:
        with connection.cursor() as cursor:
            # Clear existing static GTFS data so the script
            # can safely be rerun.
            print("\nClearing existing GTFS data...")

            cursor.execute("""
                TRUNCATE TABLE
                    stop_times,
                    trips,
                    stops,
                    routes
                CASCADE;
            """)

            # Foreign-key order matters.
            load_routes(cursor)
            load_stops(cursor)
            load_trips(cursor)
            load_stop_times(cursor)

        connection.commit()
        print("\nGTFS load completed successfully.")

    except Exception:
        # Atomic loading. If something failed, undo entire load.
        connection.rollback()
        print("\nGTFS load failed. Changes rolled back.")
        raise

    finally:
        connection.close()

if __name__ == "__main__":
    load_gtfs()