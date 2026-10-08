from idlelib.iomenu import encoding
from pathlib import Path
from datetime import datetime, timezone
import json
import os

import psycopg
from dotenv import load_dotenv

from database.test_pg_connection import connection

# ============================================================
# PROJECT PATHS
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent

load_dotenv(PROJECT_ROOT / ".env")

RAW_DATA_DIR = PROJECT_ROOT / "data" / "raw"

# ============================================================
# DATABASE SETTINGS
# ============================================================

DB_HOST = os.getenv("POSTGRES_HOST")
DB_PORT = os.getenv("POSTGRES_PORT")
DB_NAME = os.getenv("POSTGRES_DB")
DB_USER = os.getenv("POSTGRES_USER")
DB_PASSWORD = os.getenv("POSTGRES_PASSWORD")

# ============================================================
# HELPER FUNCTIONS
# ============================================================

def get_relationship_id(relationships, relationship_name):
    """
    This function safely extracts an ID from an MBTA relationship.

    Example:
    relationships["route"]["data"]["id"]
    """
    relationship = relationships.get(relationship_name)

    if not relationship:
        return None

    data = relationship.get("data")

    if not data:
        return None

    return data.get("id")

def get_collected_at(file_path):
    """
    This function uses the file's saved timestamp as the collection time.

    File modification times are stored as an absolute timestamp,
    so converting them to UTC gives us a timezone-aware datetime.
    """

    timestamp = file_path.stat().st_mtime

    return datetime.fromtimestamp(
        timestamp,
        tz=timezone.utc
    )

# ============================================================
# TRANSFORM ONE VEHICLE
# ============================================================

def transform_vehicle(vehicle, collected_at):
    attributes = vehicle.get("attributes", {})
    relationships = vehicle.get("relationships", {})

    vehicle_id = vehicle.get("id")

    if vehicle_id is None:
        return None

    transformed_vehicle = {
        "vehicle_id": vehicle_id,
        "route_id": get_relationship_id(
            relationships,
            "route"
        ),

        "trip_id": get_relationship_id(
            relationships,
            "trip"
        ),

        "stop_id": get_relationship_id(
            relationships,
            "stop"
        ),

        "latitude": attributes.get("latitude"),
        "longitude": attributes.get("longitude"),
        "bearing": attributes.get("bearing"),
        "speed": attributes.get("speed"),
        "direction_id": attributes.get("direction_id"),
        "current_status": attributes.get("current_status"),
        "current_stop_sequence": attributes.get("current_stop_sequence"),
        "occupancy_status": attributes.get("occupancy_status"),
        "vehicle_updated_at": attributes.get("updated_at"),
        "collected_at": collected_at
    }
    return transformed_vehicle

# ============================================================
# READ + TRANSFORM ONE SNAPSHOT
# ============================================================

def transform_snapshot(file_path):
    with file_path.open(
        mode="r",
        encoding="utf-8"
    ) as file:
        raw_json = json.load(file)

    # vehicles = raw_json.get("data", [])
    #
    # collected_at = get_collected_at(file_path)

    vehicles = raw_json.get("data", [])

    print("Raw vehicles found:", len(vehicles))

    if vehicles:
        print("First vehicle ID:", vehicles[0].get("id"))

    collected_at = get_collected_at(file_path)

    transformed_records = []
    for vehicle in vehicles:
        record = transform_vehicle(
            vehicle,
            collected_at
        )

        if record is not None:
            transformed_records.append(record)

    return transformed_records

# ============================================================
# LOAD RECORDS INTO POSTGRESQL
# ============================================================

def load_vehicle_records(cursor, records):
    if not records:
        return 0

    with cursor.copy("""
        COPY vehicle_positions (
            vehicle_id,
            route_id,
            trip_id,
            stop_id,
            latitude,
            longitude,
            bearing,
            speed,
            direction_id,
            current_status,
            current_stop_sequence,
            occupancy_status,
            vehicle_updated_at,
            collected_at
        )
        FROM STDIN
    """) as copy:

        for record in records:
            copy.write_row([
                record["vehicle_id"],
                record["route_id"],
                record["trip_id"],
                record["stop_id"],
                record["latitude"],
                record["longitude"],
                record["bearing"],
                record["speed"],
                record["direction_id"],
                record["current_status"],
                record["current_stop_sequence"],
                record["occupancy_status"],
                record["vehicle_updated_at"],
                record["collected_at"]
            ])

    return len(records)

# ============================================================
# PROCESS ALL VEHICLE SNAPSHOTS
# ============================================================

def load_vehicle_snapshots():
    print("Searching for vehicle snapshots...")

    vehicle_files = sorted(
        RAW_DATA_DIR.rglob("vehicles_*.json")
    )

    if not vehicle_files:
        print("No vehicle snapshot files found.")
        return

    print(
        f"Found {len(vehicle_files)} "
        f"vehicle snapshot file(s)."
    )
    print("\nConnecting to PostgreSQL...")

    connection = psycopg.connect(
        host=DB_HOST,
        port=DB_PORT,
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD
    )

    print("Connected.")

    total_records = 0

    try:
        with connection.cursor() as cursor:
            # For Step 13 we rebuild the vehicle fact table
            # from all currently saved snapshots.
            #
            # This lets us safely rerun this script without
            # creating duplicate rows.
            print("\nClearing existing vehicle positions...")

            cursor.execute("""
                TRUNCATE TABLE vehicle_positions
                RESTART IDENTITY;
            """)

            for file_path in vehicle_files:
                print(
                    f"\nProcessing: "
                    f"{file_path.name}"
                )
                records = transform_snapshot(file_path)
                loaded= load_vehicle_records(cursor, records)
                total_records += loaded

                print(
                    f"Loaded {loaded:,} "
                    f"vehicle observations."
                )

        connection.commit()

        print(f"\nVehicle load completed successfully.")
        print(
            f"Total observations loaded: "
            f"{total_records:,}"
        )
    except Exception:
        connection.rollback()
        print("\nVehicle load failed. Changes rolled back.")
        raise
    finally:
        connection.close()

if __name__ == "__main__":
    load_vehicle_snapshots()