import logging
from logging_config import setup_logging

from ingestion.realtime.alerts import collect_alerts
from ingestion.realtime.predictions import collect_predictions
from ingestion.realtime.vehicles import collect_vehicles

logger = logging.getLogger(__name__)

def run_collectors():
    logger.info(
        "========== MBTA collection run started =========="
    )
    logger.info(
        "Starting vehicle collector."
    )
    try:
        collect_vehicles()
    except Exception:
        logger.exception("Unexpected error in vehicle collector.")

    logger.info(
        "Starting prediction collector."
    )
    try:
        collect_predictions()
    except Exception:
        logger.exception("Unexpected error in predictions collector.")

    logger.info(
        "Starting alert collector."
    )
    try:
        collect_alerts()
    except Exception:
        logger.exception("Unexpected error in alerts collector.")

    logger.info(
        "========== MBTA collection run finished =========="
    )

if __name__ == "__main__":
    setup_logging()
    run_collectors()