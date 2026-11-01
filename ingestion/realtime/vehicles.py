import json
import os
import logging
from pathlib import Path
from datetime import datetime, timezone
import requests
from dotenv import load_dotenv
from streaming.producer import send_vehicle, flush_producer

# Logging
logger = logging.getLogger(__name__)

# Project root:
# ingestion/alerts.py -> parent = ingestion -> parent = project root
PROJECT_ROOT = Path(__file__).resolve().parents[2]

# Reads variables in .env file | Load .env from the project root.
load_dotenv(PROJECT_ROOT / ".env")

# Finds value in .env file (your API key).
API_KEY = os.getenv("MBTA_API_KEY")

url = "https://api-v3.mbta.com/vehicles"

my_params = {
    "filter[route]": "Red"
}

# Creates a python dict.
my_headers = {
    "x-api-key": API_KEY
}

def collect_vehicles():
    # ==============================
    # API try/except.
    # ==============================
    try:
        response = requests.get(
            url,
            params=my_params,
            headers=my_headers,
            timeout=30
        )

        response.raise_for_status()
        data = response.json()
        collected_at = datetime.now(timezone.utc)

        logger.info("Vehicle API request successful.")

        records = data.get("data", [])

        logger.info("Vehicle API returned %d records.",
                    len(records))

    except requests.RequestException as error:
        logger.error("Vehicle API request failed: %s",
            error
        )
        return

    # ==============================
    # File writing try/except.
    # ==============================
    try:
        # Create data/raw/"" if it does not exist.
        output_folder = PROJECT_ROOT / "data" / "raw" / "vehicles"
        output_folder.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S") # Windows does not allow colons.

        filename = output_folder / f"vehicles_{timestamp}.json"

        with open(filename, "w", encoding="utf-8") as file:
            json.dump(data, file, indent=2)

        logger.info("Vehicle snapshot saved: %s",
                    filename)

    except OSError as error:
        logger.error("Failed to save vehicle snapshot: %s",
                     error)
        return
    #==============================
    # Send vehicle records to Kafka.
    # ==============================
    try:
        logger.info("Publishing %d vehicle records to Kafka.",
                    len(records)
        )

        for vehicle in records:
            send_vehicle(vehicle, collected_at)

        remaining_messages = flush_producer()

        if remaining_messages == 0:
            logger.info("Published %d vehicle records to Kafka successfully.",
                        len(records)
            )
    except Exception:
        logger.exception(
            "Unexpected error while publishing vehicles to Kafka."
        )

    # ==============================
    # Return filename
    # ==============================
    return filename

if __name__ == "__main__":
    collect_vehicles()