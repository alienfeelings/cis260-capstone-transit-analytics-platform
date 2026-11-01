import json
import os
import logging
from pathlib import Path
from datetime import datetime, timezone
import requests
from dotenv import load_dotenv

from streaming.producer import (
    send_alert,
    flush_producer
)

#Logging
logger = logging.getLogger(__name__)

# Project root:
# ingestion/alerts.py -> parent = ingestion -> parent = project root
PROJECT_ROOT = Path(__file__).resolve().parents[2]

# Reads variables in .env file | Load .env from the project root.
load_dotenv(PROJECT_ROOT / ".env")

# Finds value in .env file (your API key).
API_KEY = os.getenv("MBTA_API_KEY")

url = "https://api-v3.mbta.com/alerts"

my_params = {
    "filter[route]": "Red"
}

# Creates a python dict.
my_headers = {
    "x-api-key": API_KEY
}

def collect_alerts():
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

        logger.info("Alert API request successful.")

        records = data.get("data", [])

        logger.info("Alert API returned %d records.",
                    len(records))

    except requests.RequestException as error:
        logger.error("Alert API request failed: %s",
             error
         )
        return

    try:
        # Create data/raw/alerts if it does not exist.
        output_folder = PROJECT_ROOT / "data" / "raw" / "alerts"
        output_folder.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S") # Windows does not allow colons.

        filename = output_folder / f"alerts_{timestamp}.json"

        with open(filename, "w", encoding="utf-8") as file:
            json.dump(data, file, indent=2)

        logger.info("Alert snapshot saved: %s",
                    filename)

    except OSError as error:
        logger.error("Failed to save alert snapshot: %s",
                     error)
        return

    try:
        logger.info(
            "Publishing %d alert records to Kafka.",
            len(records)
        )

        for alert in records:
            send_alert(
                alert,
                collected_at
            )

        remaining_messages = flush_producer()

        if remaining_messages == 0:
            logger.info(
                "Published %d alert records to Kafka successfully.",
                len(records)
            )
    except Exception:
        logger.exception(
            "Unexpected error while publishing alerts to Kafka."
        )

    return filename

if __name__ == "__main__":
    collect_alerts()
