import time
from datetime import datetime

from ingestion.realtime.alerts import collect_alerts
from ingestion.realtime.predictions import collect_predictions
from ingestion.realtime.vehicles import collect_vehicles

INTERVAL_SECONDS = 60

def run_collectors():
    print()
    print("=" * 60)
    print(f"Collection started: {datetime.now()}")
    print("=" * 60)

    collect_vehicles()
    collect_predictions()
    collect_alerts()

    print("Collection cycle complete.")

if __name__ == "__main__":
    try:
        while True:
            run_collectors()

            print(
                f"Waiting {INTERVAL_SECONDS} seconds before next collection..."
            )

            time.sleep(INTERVAL_SECONDS)

    except KeyboardInterrupt:
        print()
        print("Collector stopped by user.")