from pathlib import Path
from datetime import datetime, timezone
import os
import json

import psycopg
from dotenv import load_dotenv
from psycopg.types.json import Jsonb

from transformations.predictions_transform import RAW_DATA_DIR

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
def get_collected_at(file_path):
    """
    This function uses the snapshot file's modification time
    as the approximate time when the pipeline collected it.
    """
    timestamp = file_path.stat().st_mtime

    return datetime.fromtimestamp(
        timestamp,
        tz=timezone.utc
    )

def get_route_id(alert):
    """
    This function looks through the alert's informed entities
    and returns the first route ID associated with the alert.

    It returns None when no route is associated with the alert.
    """
    attributes = alert.get("attributes", {})

    informed_entities = attributes.get(
        "informed_entity",[]
    )

    for entity in informed_entities:
        route = entity.get("route")
        if route:
            return route

    return None

# ============================================================
# TRANSFORM ONE ALERT
# ============================================================
def transform_alert(alert, collected_at):
    attributes = alert.get("attributes", {})
    alert_id = alert.get("id")

    if alert_id is None:
        return None

    transformed_alert = {
        "alert_id": alert_id,
        "route_id": get_route_id(alert),
        "cause":
            attributes.get("cause"),
        "effect":
            attributes.get("effect"),
        "severity":
            attributes.get("severity"),
        "header":
            attributes.get("header"),
        "description":
            attributes.get("description"),
        "lifecycle":
            attributes.get("lifecycle"),
        "created_at":
            attributes.get("created_at"),
        "updated_at":
            attributes.get("updated_at"),
        "collected_at":
            collected_at,
        "raw_json":
            alert
    }
    return transformed_alert
# ============================================================
# READ + TRANSFORM ONE SNAPSHOT
# ============================================================
def transform_snapshot(file_path):
    with file_path.open(
        mode="r",
        encoding="utf-8"
    ) as file:
        raw_json = json.load(file)

    alerts = raw_json.get("data", []) # retrieves the actual list of alerts returned by MBTA.
    collected_at = get_collected_at(file_path)

    transformed_records = []
    for alert in alerts:
        record = transform_alert(
            alert,
            collected_at
        )
        if record is not None:
            transformed_records.append(record)

    return transformed_records
# ============================================================
# LOAD RECORDS INTO POSTGRESQL
# ============================================================
def load_alert_records(cursor, records):
    if not records:
        return 0

    with cursor.copy("""
        COPY alerts (
            alert_id,
            route_id,
            cause,
            effect,
            severity,
            header,
            description,
            lifecycle,
            created_at,
            updated_at,
            collected_at,
            raw_json
        )
        FROM STDIN
    """) as copy:

        for record in records:
            copy.write_row([
                record["alert_id"],
                record["route_id"],
                record["cause"],
                record["effect"],
                record["severity"],
                record["header"],
                record["description"],
                record["lifecycle"],
                record["created_at"],
                record["updated_at"],
                record["collected_at"],

                Jsonb(record["raw_json"])
            ])
            # Jsonb(...) tells psycopg:
            # Convert this Python dictionary into PostgreSQL JSONB
        return len(records)

# ============================================================
# PROCESS ALL ALERT SNAPSHOTS
# ============================================================
def load_alert_snapshots():
    print("Searching for alert snapshots...")
    alert_files = sorted(
        RAW_DATA_DIR.rglob("alerts_*.json")
    )

    if not alert_files:
        print("No alert snapshot files found.")
        return

    print(
        f"Found {len(alert_files)} "
        f"alert snapshot file(s)."
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
            print("\nClearing existing alerts...")

            cursor.execute("""
                TRUNCATE TABLE alerts
                RESTART IDENTITY;
            """)

            for file_path in alert_files:
                print(f"\nProcessing: {file_path.name}")

                records = transform_snapshot(file_path)
                loaded = load_alert_records(cursor, records)
                total_records += loaded

                print(f"Loaded {loaded:,} alert observations.")

        connection.commit()

        print("\nAlert load completed successfully.")

        print(f"Total observations loaded: {total_records:,}")

    except Exception:
        connection.rollback()
        print( "\nAlert load failed. Changes rolled back.")
        raise

    finally:
        connection.close()

if __name__ == "__main__":
    load_alert_snapshots()