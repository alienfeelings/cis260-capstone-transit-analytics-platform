-- ============================================================
-- PREDICTION DELAY METRICS
-- ============================================================
-- views is creating objects that will aid dashboard analytics
--A CREATE VIEW statement doesn't display a result table like a SELECT. It creates the object in PostgreSQL.

CREATE OR REPLACE VIEW prediction_delay_metrics AS

WITH prediction_schedule AS (
    SELECT
        p.prediction_observation_id,
        p.prediction_id,
        p.route_id,
        p.trip_id,

        t.trip_headsign,
        t.direction_id,

        p.stop_id,
        s.stop_name,
        p.stop_sequence,

        st.arrival_time AS scheduled_arrival_time,
        p.arrival_time AS predicted_arrival_time,

        st.departure_time AS scheduled_departure_time,
        p.departure_time AS predicted_departure_time,

        p.schedule_relationship,
        p.collected_at

    FROM predictions AS p

    LEFT JOIN trips AS t
        ON p.trip_id = t.trip_id

    LEFT JOIN stop_times AS st
        ON p.trip_id = st.trip_id
        AND p.stop_id = st.stop_id
        AND p.stop_sequence = st.stop_sequence

    LEFT JOIN stops AS s
        ON p.stop_id = s.stop_id
),

schedule_seconds AS (
    SELECT *,
        CASE
            WHEN scheduled_arrival_time IS NOT NULL
            THEN
                split_part(scheduled_arrival_time, ':', 1)::INTEGER * 3600
                +
                split_part(scheduled_arrival_time, ':', 2)::INTEGER * 60
                +
                split_part(scheduled_arrival_time, ':', 3)::INTEGER
        END AS scheduled_arrival_seconds,

        CASE
            WHEN scheduled_departure_time IS NOT NULL
            THEN
                split_part(scheduled_departure_time, ':', 1)::INTEGER * 3600
                +
                split_part(scheduled_departure_time, ':', 2)::INTEGER * 60
                +
                split_part(scheduled_departure_time, ':', 3)::INTEGER
        END AS scheduled_departure_seconds

    FROM prediction_schedule
),

candidate_times AS (
    SELECT *,
        predicted_arrival_time
            AT TIME ZONE 'America/New_York'
            AS predicted_arrival_local,

        predicted_departure_time
            AT TIME ZONE 'America/New_York'
            AS predicted_departure_local,

        date_trunc(
            'day',
            predicted_arrival_time
                AT TIME ZONE 'America/New_York'
        )
        +
        scheduled_arrival_seconds * INTERVAL '1 second'
            AS arrival_candidate_today,

        date_trunc(
            'day',
            predicted_arrival_time
                AT TIME ZONE 'America/New_York'
        )
        - INTERVAL '1 day'
        +
        scheduled_arrival_seconds * INTERVAL '1 second'
            AS arrival_candidate_yesterday,

        date_trunc(
            'day',
            predicted_departure_time
                AT TIME ZONE 'America/New_York'
        )
        +
        scheduled_departure_seconds * INTERVAL '1 second'
            AS departure_candidate_today,

        date_trunc(
            'day',
            predicted_departure_time
                AT TIME ZONE 'America/New_York'
        )
        - INTERVAL '1 day'
        +
        scheduled_departure_seconds * INTERVAL '1 second'
            AS departure_candidate_yesterday

    FROM schedule_seconds
),

resolved_schedule AS (
    SELECT *,
        CASE
            WHEN predicted_arrival_local IS NULL
                OR scheduled_arrival_seconds IS NULL
            THEN NULL

            WHEN ABS(
                EXTRACT(
                    EPOCH FROM(
                        predicted_arrival_local
                        - arrival_candidate_today
                    )
                )
            )
            <=
            ABS(
                EXTRACT(
                    EPOCH FROM(
                        predicted_arrival_local
                        - arrival_candidate_yesterday
                    )
                )
            )
            THEN arrival_candidate_today

            ELSE arrival_candidate_yesterday

        END AS scheduled_arrival_timestamp,

        CASE
            WHEN predicted_departure_local IS NULL
                OR scheduled_departure_seconds IS NULL
            THEN NULL

            WHEN ABS(
                EXTRACT(
                    EPOCH FROM(
                        predicted_departure_local
                        - departure_candidate_today
                    )
                )
            )
            <=
            ABS(
                EXTRACT(
                    EPOCH FROM(
                        predicted_departure_local
                        - departure_candidate_yesterday
                    )
                )
            )

            THEN departure_candidate_today

            ELSE departure_candidate_yesterday

        END AS scheduled_departure_timestamp

    FROM candidate_times
),

delay_calculations AS (
    SELECT *,

        ROUND(
            EXTRACT(
                EPOCH FROM(
                    predicted_arrival_local
                    - scheduled_arrival_timestamp
                )
            ) / 60.0,
            2
        ) AS arrival_delay_minutes,

        ROUND(
            EXTRACT(
                EPOCH FROM(
                    predicted_departure_local
                    - scheduled_departure_timestamp
                )
            ) / 60.0,
            2
        ) AS departure_delay_minutes

    FROM resolved_schedule
)

SELECT
    prediction_observation_id,
    prediction_id,

    route_id,
    trip_id,
    trip_headsign,
    direction_id,

    stop_id,
    stop_name,
    stop_sequence,

    scheduled_arrival_time,
    predicted_arrival_time,
    arrival_delay_minutes,

    CASE
        WHEN arrival_delay_minutes IS NULL
            THEN 'UNKNOWN'
        WHEN arrival_delay_minutes > 5
            THEN 'DELAYED'
        WHEN arrival_delay_minutes < -1
            THEN 'EARLY'
        ELSE 'ON TIME'
    END AS arrival_status,

    scheduled_departure_time,
    predicted_departure_time,
    departure_delay_minutes,

    schedule_relationship,
    collected_at

FROM delay_calculations;

-- ============================================================
-- ROUTE DELAY SUMMARY
-- ============================================================

CREATE OR REPLACE VIEW route_delay_summary AS

SELECT
    route_id,

    COUNT(*) FILTER (
        WHERE arrival_delay_minutes IS NOT NULL
    ) AS prediction_count,

    ROUND(
        AVG(arrival_delay_minutes),
        2
    ) AS average_delay_minutes,

    ROUND(
        MAX(arrival_delay_minutes),
        2
    ) AS maximum_delay_minutes,

    ROUND(
        MAX(arrival_delay_minutes),
        2
    ) AS minimum_delay_minutes,

    COUNT(*) FILTER (
        WHERE arrival_status = 'DELAYED'
    ) AS delayed_prediction_count,

    ROUND(
        100.0
        *
        COUNT(*) FILTER (
            WHERE arrival_status = 'DELAYED'
        )
        /
        NULLIF(
            COUNT(*) FILTER (
                WHERE arrival_delay_minutes IS NOT NULL
            ),
            0
        ),
        2
    ) AS delayed_percentage

FROM prediction_delay_metrics
GROUP BY route_id;

-- ============================================================
-- STOP DELAY SUMMARY
-- ============================================================

CREATE OR REPLACE VIEW stop_delay_summary AS

SELECT
    route_id,
    stop_id,
    stop_name,

    COUNT(*) FILTER (
        WHERE arrival_delay_minutes IS NOT NULL
    ) AS prediction_count,

    ROUND(
        AVG(arrival_delay_minutes),
        2
    ) AS average_delay_minutes,

    ROUND(
        AVG(arrival_delay_minutes),
        2
    ) AS maximum_delay_minutes,

    COUNT(*) FILTER (
        WHERE arrival_status = 'DELAYED'
    ) AS delayed_prediction_count

FROM prediction_delay_metrics
GROUP BY
    route_id,
    stop_id,
    stop_name;

-- ============================================================
-- LATEST VEHICLE POSITIONS
-- ============================================================

CREATE OR REPLACE VIEW latest_vehicle_positions AS

SELECT
    vehicle_position_id,
    vehicle_id,
    route_id,
    trip_id,
    stop_id,

    latitude,
    longitude,
    bearing,
    speed,

    direction_id,
    current_status,
    current_stop_sequence,
    occupancy_status,

    vehicle_updated_at,
    collected_at

FROM vehicle_positions

WHERE collected_at = (
    SELECT MAX(collected_at)
    FROM vehicle_positions
);

-- ============================================================
-- LATEST ALERT OBSERVATIONS
-- ============================================================

CREATE OR REPLACE VIEW latest_alerts AS

SELECT DISTINCT ON (alert_id)

    alert_observation_id,
    alert_id,
    route_id,

    cause,
    effect,
    severity,

    header,
    description,
    lifecycle,

    created_at,
    updated_at,
    collected_at,

    raw_json

FROM alerts

ORDER BY
    alert_id,
    collected_at DESC;

