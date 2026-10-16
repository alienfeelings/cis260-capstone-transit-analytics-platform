import logging
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parent
LOG_DIR = PROJECT_ROOT / "logs"
LOG_FILE = LOG_DIR / "pipeline.log"

LOG_DIR.mkdir(exist_ok=True)

def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        handlers=[
            logging.FileHandler( # writes messages into LOG_FILE.
                LOG_FILE,
                encoding="utf-8"
            ),
            # shows those messages in your terminal.
            # logging.StreamHandler(sys.stdout) colors output logging from red to std white (also applies to errors)
            logging.StreamHandler()
        ]
    )