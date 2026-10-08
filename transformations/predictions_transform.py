from idlelib.iomenu import encoding
from pathlib import Path
from datetime import datetime, timezone
import json
import os

import psycopg
from dotenv import load_dotenv

from transformations.vehicles_transform import RAW_DATA_DIR

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
    This function extracts an ID from an MBTA relationship.
    It returns None when the relationship does not contain data.
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
     This function uses the snapshot file's modification time
     as the approximate time when our pipeline collected it.
     """
    timestamp = file_path.stat().st_mtime

    return datetime.fromtimestamp(
        timestamp,
        tz=timezone.utc
    )

# ============================================================
# TRANSFORM ONE PREDICTION
# ============================================================

def transform_prediction(prediction, collected_at):
    attributes = prediction.get("attributes", {})
    relationships = prediction.get("relationships", {})

    prediction_id = prediction.get("id")

    if prediction_id is None:
        return None

    transformed_prediction = {
        "prediction_id": prediction_id,

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

        "vehicle_id": get_relationship_id(
            relationships,
            "vehicle"
        ),

        "arrival_time": attributes.get("arrival_time"),
        "departure_time": attributes.get("departure_time"),

        "arrival_uncertainty":
            attributes.get("arrival_uncertainty"),

        "departure_uncertainty":
            attributes.get("departure_uncertainty"),

        "direction_id":
            attributes.get("direction_id"),

        "stop_sequence":
            attributes.get("stop_sequence"),

        "status":
            attributes.get("status"),

        "schedule_relationship":
            attributes.get("schedule_relationship"),

        "collected_at": collected_at
    }
    return transformed_prediction
# ============================================================
# READ + TRANSFORM ONE SNAPSHOT
# ============================================================
def transform_snapshot(file_path):
    with file_path.open(
        mode="r",
        encoding="utf-8"
    ) as file:
        raw_json = json.load(file)

    predictions = raw_json.get("data", [])
    collected_at = get_collected_at(file_path)

    transformed_records = []
    for prediction in predictions:
        record = transform_prediction(
            prediction,
            collected_at
        )
        if record is not None:
            transformed_records.append(record)

    return transformed_records

# ============================================================
# LOAD RECORDS INTO POSTGRESQL
# ============================================================
def load_prediction_records(cursor, records):

    if not records:
        return 0

    with cursor.copy("""
        COPY predictions (
            prediction_id,
            route_id,
            trip_id,
            stop_id,
            vehicle_id,
            arrival_time,
            departure_time,
            arrival_uncertainty,
            departure_uncertainty,
            direction_id,
            stop_sequence,
            status,
            schedule_relationship,
            collected_at
        )
        FROM STDIN
    """) as copy:

        for record in records:

            copy.write_row([
                record["prediction_id"],
                record["route_id"],
                record["trip_id"],
                record["stop_id"],
                record["vehicle_id"],
                record["arrival_time"],
                record["departure_time"],
                record["arrival_uncertainty"],
                record["departure_uncertainty"],
                record["direction_id"],
                record["stop_sequence"],
                record["status"],
                record["schedule_relationship"],
                record["collected_at"]
            ])

    return len(records)

# ============================================================
# PROCESS ALL PREDICTION SNAPSHOTS
# ============================================================
def load_prediction_snapshots():

    print("Searching for prediction snapshots...")

    prediction_files = sorted(
        RAW_DATA_DIR.rglob("predictions_*.json")
    )

    if not prediction_files:
        print("No prediction snapshot files found.")
        return

    print(
        f"Found {len(prediction_files)} "
        f"prediction snapshot file(s)."
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
            print("\nClearing existing predictions...")

            cursor.execute("""
                TRUNCATE TABLE predictions
                RESTART IDENTITY;
            """)

            for file_path in prediction_files:

                print(
                    f"\nProcessing: "
                    f"{file_path.name}"
                )
                records = transform_snapshot(file_path)
                loaded = load_prediction_records(
                    cursor,
                    records
                )
                total_records += loaded

                print(
                    f"Loaded {loaded:,} "
                    f"prediction observations."
                )

        connection.commit()

        print(
            "\nPrediction load completed successfully."
        )
        print(
            f"Total observations loaded: "
            f"{total_records:,}"
        )

    except Exception:
        connection.rollback()
        print(
            "\nPrediction load failed. "
            "Changes rolled back."
        )
        raise

    finally:
        connection.close()


if __name__ == "__main__":
    load_prediction_snapshots()