# MBTA Data Pipeline & Analytics Platform 

## 1. Overview

An end-to-end platform that continuously ingests 
MBTA realtime and static GTFS data, processes vehicle and trip 
events, stores both raw and processed data in PostgreSQL, 
and provides dashboards for analyzing transit performance. 

## 2. Architecture

MBTA API + GTFS → Python ingestion → 
JSON snapshots → ETL/loaders → PostgreSQL → 
analytics layer → Streamlit/dashboard

## 3. Tech Stack

Python 3.12, PostgreSQL, psycopg, requests, 
python-dotenv, MBTA V3 API, GTFS, and eventually Streamlit.

## 4. Repository Structure

- PROJECT_ROOT
    - PROJECT_ROOT/ingestion/realtime/\
      - Ingestion files that pull MBTA V3 API live data & create JSON snapshot
    - PROJECT_ROOT/ingestion/static/load_gtfs.py\
      - loads static GTFS data into PostgreSQL
    - PROJECT_ROOT/database/create_schema.py/\
      - database schema creation .py file
    - PROJECT_ROOT/database/schema.sql/\
      - database schema structure
    - PROJECT_ROOT/analytics/*.sql/\
      - PostgreSQL relationship logic
    - PROJECT_ROOT/data/raw/
      - /alerts/
      - /predictions/
      - /vehicles/\
        - JSON snapshots stored here
    - PROJECT_ROOT/data/gtfs/*.txt/
      - GTFS static data .txt files
    - PROJECT_ROOT/transformations/*.py/
      - reads JSON, transforms and loads them into postgreSQL
    - PROJECT_ROOT/tests/
      - API test files
    - .env
    - requirements.txt
    - README.md

## 5. Data Sources

This project uses the MBTA V3 API for realtime transit data and the MBTA GTFS feed for static schedule data.

#### MBTA Realtime API

Base URL:

`https://api-v3.mbta.com`

The pipeline uses the following endpoints:

| Endpoint | Purpose |
|---|---|
| `GET /vehicles` | Retrieves realtime vehicle locations and status information. |
| `GET /predictions` | Retrieves predicted arrival and departure times for MBTA service. |
| `GET /alerts` | Retrieves active service alerts, delays, closures, and other disruptions. |
| `GET /routes` | Retrieves MBTA route information. |
| `GET /stops` | Retrieves stop and station information. |
| `GET /schedules` | Retrieves scheduled arrival and departure information. |

Most realtime collection in the current implementation is filtered to the MBTA Red Line using:

`filter[route]=Red`

API authentication is performed using the MBTA API key in the request header:

`x-api-key: <MBTA_API_KEY>`

## 6. Environment Configuration

Environment configuration (.env) is as follows:

MBTA_API_KEY="unique_api_key"

POSTGRES_HOST=localhost\
POSTGRES_PORT=5432\
POSTGRES_DB=mbta_pipeline\
POSTGRES_USER=postgres\
POSTGRES_PASSWORD="password"

#### Notes
* .env file must never be committed and it must be listed under .gitignore file.
* You must obtain a unique API key ("unique_api_key") from the MBTA V3 webpage:
  * https://api-v3.mbta.com/
* Password is "postgres" by default unless you've created your own.

## 7. Local Setup

#### Bash

git clone <repository-url>\
cd "PROJECT_ROOT"

python -m venv .venv

#### Windows/PyCharm
.venv\Scripts\activate\
pip install -r requirements.txt

### PostgreSQL Database Setup

This project uses PostgreSQL as the primary relational database for storing static GTFS data and realtime MBTA observations.

#### Prerequisites

Install PostgreSQL locally and ensure the PostgreSQL service is running.

The current development environment uses PostgreSQL 18, although the project should work with other recent PostgreSQL versions.

#### Create the Database

Create a local PostgreSQL database named:

```text
mbta_pipeline
```

You can create the database through pgAdmin or with the PostgreSQL command line:

```sql
CREATE DATABASE mbta_pipeline;
```

#### Environment Variables

Database credentials are stored in a project-level `.env` file.

Create a `.env` file in the project root and define the following variables:

```env
MBTA_API_KEY=your_mbta_api_key

POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=mbta_pipeline
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your_postgres_password
```

Do not commit the `.env` file to version control.

The application loads these values using `python-dotenv`.

#### Database Connection

Python scripts connect to PostgreSQL using `psycopg`.

Database configuration is loaded from environment variables rather than being hard-coded into the source code.

Example configuration:

```python
DB_HOST = os.getenv("POSTGRES_HOST")
DB_PORT = os.getenv("POSTGRES_PORT")
DB_NAME = os.getenv("POSTGRES_DB")
DB_USER = os.getenv("POSTGRES_USER")
DB_PASSWORD = os.getenv("POSTGRES_PASSWORD")
```

A connection is then created with:

```python
connection = psycopg.connect(
    host=DB_HOST,
    port=DB_PORT,
    dbname=DB_NAME,
    user=DB_USER,
    password=DB_PASSWORD
)
```

#### Test the Connection

Before creating the schema or loading data, verify that the application can connect to PostgreSQL:

```bash
python database/test_connection.py
```

A successful connection confirms that:

- PostgreSQL is running
- the `mbta_pipeline` database exists
- the credentials in `.env` are correct
- the Python environment can connect through `psycopg`

#### Create the Database Schema

Once the database connection has been verified, create the project tables:

```bash
python database/create_schema.py
```

This script creates the tables required for the pipeline, including tables used for static GTFS data and realtime observations.

Run this step before attempting to load GTFS or realtime data.

#### Load Static GTFS Data

After the schema has been created, load the MBTA GTFS dataset into PostgreSQL:

```bash
python database/load_gtfs.py
```

The GTFS loader populates static transit tables including:

- `routes`
- `stops`
- `trips`
- `stop_times`

#### Load Realtime Data

Realtime MBTA API responses are first stored as JSON snapshots. Separate loader scripts transform those snapshots and insert them into PostgreSQL.

Run the loaders with:

```bash
python database/load_vehicles.py
python database/load_predictions.py
python database/load_alerts.py
```

The expected setup order is therefore:

```text
Install PostgreSQL
        ↓
Create mbta_pipeline database
        ↓
Configure .env
        ↓
Test database connection
        ↓
Run create_schema.py
        ↓
Load GTFS static data
        ↓
Collect realtime JSON snapshots
        ↓
Load realtime observations into PostgreSQL
```

#### Common Connection Issues

If PostgreSQL returns:

```text
psycopg.OperationalError: no password supplied
```

verify that `POSTGRES_PASSWORD` is defined in `.env` and that the application is loading the project-level `.env` file.

If authentication fails, verify that the username and password match the PostgreSQL credentials configured locally.

If a loader returns an error such as:

```text
relation "stop_times" does not exist
```

run:

```bash
python database/create_schema.py
```

before running the data loaders.

## 8. Pipeline Execution

The pipeline is executed in stages. Static GTFS data should be loaded before realtime observations so that reference data such as routes, stops, and trips is available in PostgreSQL.

### a. Verify the PostgreSQL Connection

Ensure PostgreSQL is running and the required database credentials are configured in the project-level `.env` file.

Run:

**bash**\
PROJECT_ROOT/database/test_pg_connection.py

### b. Create the Database Schema

PROJECT_ROOT/database/create_schema.py\
Stored in: database/schema.sql

### c. Load Static GTFS Data

PROJECT_ROOT/ingestion/static/load_gtfs.py\
Stored in: data/gtfs/

### d. Collect Realtime MBTA Data

Run collectors individually:\
PROJECT_ROOT/ingestion/realtime/vehicles.py\
PROJECT_ROOT/ingestion/realtime/predictions.py\
PROJECT_ROOT/ingestion/realtime/alerts.py

Raw JSON snapshots are stored in:\
PROJECT_ROOT/data/raw/vehicles/\
PROJECT_ROOT/data/raw/predictions/\
PROJECT_ROOT/data/raw/alerts/

### e. Transform and Load Realtime Observations

After snapshots have been collected, run transformation scripts:\
PROJECT_ROOT/transformations/vehicles_transform.py\
PROJECT_ROOT/transformations/predictions_transform.py\
PROJECT_ROOT/transformations/alerts_transform.py

### Initial Setup

Only follow these steps if setting up project for the first time
or rebuilding database:\

PROJECT_ROOT/database/test_pg_connection.py\
PROJECT_ROOT/database/create_schema.py\
PROJECT_ROOT/ingestion/static/load_gtfs.py

Setup process:\
Create database > 
Configure environment variables >
Test PostgreSQL connection >
Create schema >
Load static GTFS data

### Normal Pipeline Run

Once the database schema and GTFS data already exist, a typical development run only requires collecting 
new realtime data and loading the resulting observations.

PROJECT_ROOT/ingestion/realtime/vehicles.py\
PROJECT_ROOT/ingestion/realtime/predictions.py\
PROJECT_ROOT/ingestion/realtime/alerts.py

PROJECT_ROOT/transformations/vehicles_transform.py\
PROJECT_ROOT/transformations/predictions_transform.py\
PROJECT_ROOT/transformations/alerts_transform.py

Normal execution of flow is:
Collect realtime MBTA data >
Save timestamped JSON snapshots >
Transform raw API responses >
Load observations into PostgreSQL >\
Run analytics

## 9. Troubleshooting

Please refer to PROJECT_ROOT/ERROR_LOG.md
