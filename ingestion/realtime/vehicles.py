import json
import os
from pathlib import Path
from datetime import datetime
import requests
from dotenv import load_dotenv

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

response = requests.get(
    url,
    params=my_params,
    headers=my_headers,
    timeout=30
)

response.raise_for_status()
data = response.json()

# Create data/raw/alerts if it does not exist.
output_folder = PROJECT_ROOT / "data" / "raw" / "vehicles"
output_folder.mkdir(parents=True, exist_ok=True)

timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S") # Windows does not allow colons.

filename = output_folder / f"vehicles_{timestamp}.json"

with open(filename, "w", encoding="utf-8") as file:
    json.dump(data, file, indent=2)

print("Current working directory:", os.getcwd())
print(f"Saved {filename}")