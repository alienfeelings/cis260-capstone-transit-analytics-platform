import json
import os
from pathlib import Path
import requests
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parents[1]

load_dotenv(PROJECT_ROOT / ".env")

API_KEY = os.getenv("MBTA_API_KEY")

url = "https://api-v3.mbta.com/routes"

my_headers = {
    "x-api-key": API_KEY
}

response = (requests.get(
    url,
    headers=my_headers,
    timeout=30
))

response.raise_for_status()
data = response.json()

print(json.dumps(data, indent=2))
