import json
import os
import logging
from pathlib import Path
from datetime import datetime, timezone
import requests
from dotenv import load_dotenv

from streaming.producer import (
    send_prediction,
    flush_producer
)

# Logging
logger = logging.getLogger(__name__)

# Project root:
# ingestion/alerts.py -> parent = ingestion -> parent = project root
PROJECT_ROOT = Path(__file__).resolve().parents[2]

# Reads variables in .env file | Load .env from the project root.
load_dotenv(PROJECT_ROOT / ".env")

# Finds value in .env file (your API key).
API_KEY = os.getenv("MBTA_API_KEY")

url = "https://api-v3.mbta.com/predictions"

my_params = {
    "filter[route]": "Red"
}

# Creates a python dict.
my_headers = {
    "x-api-key": API_KEY
}

def collect_predictions():
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

        logger.info("Prediction API request successful.")

        records = data.get("data", [])

        logger.info("Prediction API returned %d records.",
                    len(records))

    except requests.RequestException as error:
        logger.error(
            "Prediction API request failed: %s",
            error
        )
        return

    try:
        # Create data/raw/"" if it does not exist.
        output_folder = PROJECT_ROOT / "data" / "raw" / "predictions"
        output_folder.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S") # Windows does not allow colons.

        filename = output_folder / f"predictions_{timestamp}.json"

        with open(filename, "w", encoding="utf-8") as file:
            json.dump(data, file, indent=2)

        logger.info("Prediction snapshot saved: %s",
                    filename)
    except OSError as error:
        logger.error("Failed to save prediction snapshot: %s",
                     error)
        return

    try:
        logger.info(
            "Publishing %d prediction records to Kafka.",
            len(records)
        )

        for prediction in records:
            send_prediction(
                prediction,
                collected_at
            )

        remaining_messages = flush_producer()

        if remaining_messages == 0:
            logger.info(
                "Published %d prediction records to Kafka successfully.",
                len(records)
            )
    except Exception:
        logger.exception(
            "Unexpected error while publishing predictions to Kafka."
        )

    return filename

if __name__ == "__main__":
    collect_predictions()