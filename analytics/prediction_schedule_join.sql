--from step 16
--combining 4 tables: predictions, trips, stop_times, stops
SELECT
    p.prediction_observation_id,

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

ORDER BY p.collected_at DESC

LIMIT 50;
