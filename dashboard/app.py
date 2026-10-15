from pathlib import Path
import os

import pandas as pd
import psycopg
import streamlit as st
from dotenv import load_dotenv

# ============================================================
# PAGE CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="MBTA Transit Analytics",
    page_icon="🚇",
    layout="wide"
)

# ============================================================
# PROJECT + DATABASE SETTINGS
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_ROOT / ".env")

DB_HOST = os.getenv("POSTGRES_HOST")
DB_PORT = os.getenv("POSTGRES_PORT")
DB_NAME = os.getenv("POSTGRES_DB")
DB_USER = os.getenv("POSTGRES_USER")
DB_PASSWORD = os.getenv("POSTGRES_PASSWORD")

# ============================================================
# DATABASE QUERY FUNCTION (reusable)
# ============================================================

@st.cache_data(ttl=60)
def run_query(query, params=None):

    connection = psycopg.connect(
        host=DB_HOST,
        port=DB_PORT,
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD
    )

    try:
        with connection.cursor() as cursor:
            cursor.execute(
                query,
                params
            )

            rows = cursor.fetchall()

            columns = [
                description.name
                for description
                in cursor.description
            ]
        dataframe = pd.DataFrame(
            rows,
            columns=columns
        )
        return dataframe

    finally:
        connection.close()

# ============================================================
# HEADER (title)
# ============================================================

st.title("🚇 MBTA Transit Analytics Platform")

st.caption(
    "Real-time MBTA vehicle, prediction, alert, "
    "and GTFS schedule analytics."
)

# ============================================================
# (MANUAL) REFRESH BUTTON
# This gives you a manual way to force fresh database queries after you run your collectors/loaders again.
# ============================================================

if st.button("Refresh dashboard"):
    st.cache_data_clear()
    st.rerun()

# ============================================================
# ROUTE FILTER
# ============================================================

routes_df = run_query("""
    SELECT DISTINCT route_id
    FROM prediction_delay_metrics
    WHERE route_id IS NOT NULL
    ORDER BY route_id;
""")

if routes_df.empty:
    st.error("No route analytics were found in PostgreSQL.")
    st.stop()

route_options = routes_df["route_id"].tolist()

selected_route = st.selectbox(
    "Select route",
    route_options
)

# ============================================================
# KPI DATA
# ============================================================

route_summary_df = run_query("""
    SELECT
        prediction_count,
        average_delay_minutes,
        delayed_prediction_count,
        delayed_percentage
    FROM route_delay_summary
    WHERE route_id = %s;
""", (selected_route,))

vehicle_count_df = run_query("""
    SELECT 
        COUNT(*) AS vehicle_count
    FROM latest_vehicle_positions
    WHERE route_id = %s;
""", (selected_route,))

alert_count_df = run_query("""
    SELECT 
        COUNT(*) AS alert_count
    FROM latest_alerts
    WHERE route_id = %s;
""", (selected_route,))

# EXTRACTING  VALUES

if not route_summary_df.empty:
    route_summary = route_summary_df.iloc[0]

    average_delay = route_summary[
        "average_delay_minutes"
    ]
    delayed_count = route_summary[
        "delayed_prediction_count"
    ]
    delayed_percentage = route_summary[
        "delayed_percentage"
    ]

else:
    average_delay = None
    delayed_count = 0
    delayed_percentage = None

vehicle_count = (
    vehicle_count_df.iloc[0]["vehicle_count"]
    if not vehicle_count_df.empty
    else 0
)

alert_count = (
    alert_count_df.iloc[0]["alert_count"]
    if not alert_count_df.empty
    else 0
)

# ============================================================
# KPI CARDS
# ============================================================

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(
        "Vehicle in latest snapshot",
        int(vehicle_count)
    )

with col2:
    delay_display = (
        f"{average_delay:.2f} min"
        if average_delay is not None
        else "N/A"
    )

    st.metric(
        "Average predicted delay",
        delay_display
    )

with col3:
    if delayed_percentage is not None:
        delayed_display = (
            f"{int(delayed_count)} "
            f"({delayed_percentage:.1f}%)"
        )
    else:
        delayed_display = "N/A"
    st.metric(
        "Delayed predictions",
        delayed_display
    )

with col4:
    st.metric(
        "Latest alerts",
        int(alert_count)
    )

# ============================================================
# STOP DELAY ANALYTICS (average delay by stop)
# ============================================================

st.subheader(
    "Average predicted delay by stop"
)

stop_delays_df = run_query("""
    SELECT
        stop_name,
        prediction_count,
        average_delay_minutes,
        maximum_delay_minutes
    FROM stop_delay_summary
    WHERE route_id = %s
      AND average_delay_minutes IS NOT NULL
    ORDER BY average_delay_minutes DESC;
""", (selected_route,))

if stop_delays_df.empty:
    st.info(
        "No stop delay data available for this route."
    )
else:
    chart_df = (
        stop_delays_df[
            [
                "stop_name",
                "average_delay_minutes"
            ]
        ]
        .set_index("stop_name")
    )

    st.bar_chart(
        chart_df
    )

# ============================================================
# DELAY STATUS DISTRIBUTION
# ============================================================

st.subheader(
    "Prediction status distribution"
)
status_df = run_query("""
    SELECT
        arrival_status,
        COUNT(*) AS prediction_count
    FROM prediction_delay_metrics
    WHERE route_id = %s
    GROUP BY arrival_status
    ORDER BY prediction_count DESC;
""", (selected_route,))

if not status_df.empty:
    status_chart_df = (
        status_df
        .set_index("arrival_status")
    )
    st.bar_chart(
        status_chart_df
    )

# ============================================================
# LATEST VEHICLES
# ============================================================

st.subheader("Latest vehicle positions")

vehicles_df = run_query("""
    SELECT
        vehicle_id,
        latitude,
        longitude,
        speed,
        current_status,
        vehicle_updated_at,
        collected_at
    FROM latest_vehicle_positions
    WHERE route_id = %s
      AND latitude IS NOT NULL
      AND longitude IS NOT NULL;
""", (selected_route,))

if vehicles_df.empty:
    st.info("No vehicle position data available.")
else:
    map_df = vehicles_df[
        [
            "latitude",
            "longitude"
        ]
    ].copy()

    st.map(
        map_df,
        latitude="latitude",
        longitude="longitude"
    )

st.dataframe(
    vehicles_df,
    use_container_width=True,
    hide_index=True
)

# ============================================================
# ALERTS
# ============================================================

st.subheader(
    "Latest service alerts"
)

alerts_df = run_query("""
    SELECT
        alert_id,
        cause,
        effect,
        severity,
        header,
        lifecycle,
        updated_at
    FROM latest_alerts
    WHERE route_id = %s
    ORDER BY updated_at DESC NULLS LAST;
""", (selected_route,))

if alerts_df.empty:
    st.success(
        "No alerts available for this route."
    )
else:
    st.dataframe(
        alerts_df,
        use_container_width=True,
        hide_index=True
    )

# ============================================================
# RECENT DELAY RECORDS
# ============================================================

st.subheader(
    "Recent prediction analytics"
)


recent_predictions_df = run_query("""
    SELECT
        stop_name,
        trip_headsign,
        scheduled_arrival_time,
        predicted_arrival_time,
        arrival_delay_minutes,
        arrival_status,
        collected_at
    FROM prediction_delay_metrics
    WHERE route_id = %s
    ORDER BY collected_at DESC
    LIMIT 100;
""", (selected_route,))

st.dataframe(
    recent_predictions_df,
    use_container_width=True,
    hide_index=True
)

