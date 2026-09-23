import os
from sqlite3.dbapi2 import paramstyle

import requests
from dotenv import load_dotenv

# Reads .env file.
load_dotenv()

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

response = requests.get(
    url,
    params=my_params,
    headers=my_headers
)

print("Status code:", response.status_code)
print(response.json())
