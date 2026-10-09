--from step 17
--calculating delay metrics
--handling GTFS scheduled times as they can exceed 24 hrs
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

    SELECT
        *,

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

    SELECT
        *,

        predicted_arrival_time
            AT TIME ZONE 'America/New_York'
            AS predicted_arrival_local,

        predicted_departure_time
            AT TIME ZONE 'America/New_York'
            AS predicted_departure_local,

        date_trunc(
            'day',
            predicted_arrival_time AT TIME ZONE 'America/New_York'
        )
        +
        scheduled_arrival_seconds * INTERVAL '1 second'
            AS arrival_candidate_today,

        date_trunc(
            'day',
            predicted_arrival_time AT TIME ZONE 'America/New_York'
        )
        - INTERVAL '1 day'
        +
        scheduled_arrival_seconds * INTERVAL '1 second'
            AS arrival_candidate_yesterday,

        date_trunc(
            'day',
            predicted_departure_time AT TIME ZONE 'America/New_York'
        )
        +
        scheduled_departure_seconds * INTERVAL '1 second'
            AS departure_candidate_today,

        date_trunc(
            'day',
            predicted_departure_time AT TIME ZONE 'America/New_York'
        )
        - INTERVAL '1 day'
        +
        scheduled_departure_seconds * INTERVAL '1 second'
            AS departure_candidate_yesterday

    FROM schedule_seconds
),

resolved_schedule AS (

    SELECT
        *,

        CASE
            WHEN predicted_arrival_local IS NULL
                OR scheduled_arrival_seconds IS NULL
                THEN NULL

            WHEN ABS(
                EXTRACT(
                    EPOCH FROM
                    (
                        predicted_arrival_local
                        - arrival_candidate_today
                    )
                )
            )
            <=
            ABS(
                EXTRACT(
                    EPOCH FROM
                    (
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
                    EPOCH FROM
                    (
                        predicted_departure_local
                        - departure_candidate_today
                    )
                )
            )
            <=
            ABS(
                EXTRACT(
                    EPOCH FROM
                    (
                        predicted_departure_local
                        - departure_candidate_yesterday
                    )
                )
            )

            THEN departure_candidate_today

            ELSE departure_candidate_yesterday
        END AS scheduled_departure_timestamp

    FROM candidate_times
)
, delay_calculations AS (

    SELECT
        *,

        ROUND(
            EXTRACT(
                EPOCH FROM
                (
                    predicted_arrival_local
                    - scheduled_arrival_timestamp
                )
            ) / 60.0,
            2
        ) AS arrival_delay_minutes,

        ROUND(
            EXTRACT(
                EPOCH FROM
                (
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

        ELSE 'ON_TIME'
    END AS arrival_status,

    scheduled_departure_time,
    predicted_departure_time,
    departure_delay_minutes,

    schedule_relationship,
    collected_at

FROM delay_calculations

ORDER BY collected_at DESC;