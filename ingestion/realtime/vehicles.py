import json
import os
from pathlib import Path
from datetime import datetime
import requests
from dotenv import load_dotenv

# Reads .env file.
load_dotenv()

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
    timeout=(5, 30)
)

response.raise_for_status()
data = response.json()

PROJECT_ROOT = Path(__file__).resolve().parents[2]
raw_dir = PROJECT_ROOT / "data" / "raw"

timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S") # Windows does not allow colons.
filename = raw_dir / f"vehicles_{timestamp}.json"

with open(filename, "w") as file:
    json.dump(data, file, indent=2)

print("Current working directory:", os.getcwd())
print(f"Saved {filename}")
