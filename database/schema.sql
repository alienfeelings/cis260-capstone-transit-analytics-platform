-- ============================================================
-- MBTA Transit Analytics Platform
-- Database Schema
-- ============================================================


-- ============================================================
-- STATIC / REFERENCE TABLES
-- ============================================================


-- -------------------------
-- ROUTES
-- -------------------------

CREATE TABLE IF NOT EXISTS routes (
    route_id TEXT PRIMARY KEY,
    agency_id TEXT,
    route_short_name TEXT,
    route_long_name TEXT,
    route_desc TEXT,
    route_type INTEGER,
    route_url TEXT,
    route_color TEXT,
    route_text_color TEXT,
    route_sort_order INTEGER
);


-- -------------------------
-- STOPS
-- -------------------------

CREATE TABLE IF NOT EXISTS stops (
    stop_id TEXT PRIMARY KEY,
    stop_code TEXT,
    stop_name TEXT,
    stop_desc TEXT,
    platform_code TEXT,
    platform_name TEXT,
    stop_lat DOUBLE PRECISION,
    stop_lon DOUBLE PRECISION,
    zone_id TEXT,
    stop_address TEXT,
    stop_url TEXT,
    location_type INTEGER,
    parent_station TEXT,
    wheelchair_boarding INTEGER
);


-- -------------------------
-- TRIPS
-- -------------------------

CREATE TABLE IF NOT EXISTS trips (
    trip_id TEXT PRIMARY KEY,
    route_id TEXT NOT NULL,
    service_id TEXT,
    trip_headsign TEXT,
    trip_short_name TEXT,
    direction_id INTEGER,
    block_id TEXT,
    shape_id TEXT,
    wheelchair_accessible INTEGER,

    CONSTRAINT fk_trips_route
        FOREIGN KEY (route_id)
        REFERENCES routes(route_id)
);


-- -------------------------
-- STOP TIMES
-- -------------------------

CREATE TABLE IF NOT EXISTS stop_times (
    trip_id TEXT NOT NULL,
    arrival_time TEXT,
    departure_time TEXT,
    stop_id TEXT NOT NULL,
    stop_sequence INTEGER NOT NULL,
    stop_headsign TEXT,
    pickup_type INTEGER,
    drop_off_type INTEGER,
    timepoint INTEGER,

    PRIMARY KEY (trip_id, stop_sequence),

    CONSTRAINT fk_stop_times_trip
        FOREIGN KEY (trip_id)
        REFERENCES trips(trip_id),

    CONSTRAINT fk_stop_times_stop
        FOREIGN KEY (stop_id)
        REFERENCES stops(stop_id)
);


-- ============================================================
-- REAL-TIME FACT TABLES
-- ============================================================


-- -------------------------
-- VEHICLE POSITIONS
-- -------------------------

CREATE TABLE IF NOT EXISTS vehicle_positions (
    vehicle_position_id BIGSERIAL PRIMARY KEY,

    vehicle_id TEXT NOT NULL,
    route_id TEXT,
    trip_id TEXT,
    stop_id TEXT,

    latitude DOUBLE PRECISION,
    longitude DOUBLE PRECISION,
    bearing DOUBLE PRECISION,
    speed DOUBLE PRECISION,

    direction_id INTEGER,
    current_status TEXT,
    current_stop_sequence INTEGER,
    occupancy_status TEXT,

    vehicle_updated_at TIMESTAMPTZ,
    collected_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);


-- -------------------------
-- PREDICTIONS
-- -------------------------

CREATE TABLE IF NOT EXISTS predictions (
    prediction_observation_id BIGSERIAL PRIMARY KEY,

    prediction_id TEXT NOT NULL,

    route_id TEXT,
    trip_id TEXT,
    stop_id TEXT,
    vehicle_id TEXT,

    arrival_time TIMESTAMPTZ,
    departure_time TIMESTAMPTZ,

    arrival_uncertainty INTEGER,
    departure_uncertainty INTEGER,

    direction_id INTEGER,
    stop_sequence INTEGER,
    status TEXT,
    schedule_relationship TEXT,

    collected_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);


-- -------------------------
-- ALERTS
-- -------------------------

CREATE TABLE IF NOT EXISTS alerts (
    alert_observation_id BIGSERIAL PRIMARY KEY,

    alert_id TEXT NOT NULL,
    route_id TEXT,

    cause TEXT,
    effect TEXT,
    severity INTEGER,

    header TEXT,
    description TEXT,
    lifecycle TEXT,

    created_at TIMESTAMPTZ,
    updated_at TIMESTAMPTZ,

    collected_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    raw_json JSONB
);


-- ============================================================
-- INDEXES
-- ============================================================


-- Trips
CREATE INDEX IF NOT EXISTS idx_trips_route_id
ON trips(route_id);


-- Stop Times
CREATE INDEX IF NOT EXISTS idx_stop_times_stop_id
ON stop_times(stop_id);

CREATE INDEX IF NOT EXISTS idx_stop_times_trip_id
ON stop_times(trip_id);


-- Vehicle Positions
CREATE INDEX IF NOT EXISTS idx_vehicle_positions_vehicle_id
ON vehicle_positions(vehicle_id);

CREATE INDEX IF NOT EXISTS idx_vehicle_positions_route_id
ON vehicle_positions(route_id);

CREATE INDEX IF NOT EXISTS idx_vehicle_positions_collected_at
ON vehicle_positions(collected_at);


-- Predictions
CREATE INDEX IF NOT EXISTS idx_predictions_route_id
ON predictions(route_id);

CREATE INDEX IF NOT EXISTS idx_predictions_stop_id
ON predictions(stop_id);

CREATE INDEX IF NOT EXISTS idx_predictions_trip_id
ON predictions(trip_id);

CREATE INDEX IF NOT EXISTS idx_predictions_collected_at
ON predictions(collected_at);


-- Alerts
CREATE INDEX IF NOT EXISTS idx_alerts_alert_id
ON alerts(alert_id);

CREATE INDEX IF NOT EXISTS idx_alerts_route_id
ON alerts(route_id);

CREATE INDEX IF NOT EXISTS idx_alerts_collected_at
ON alerts(collected_at);