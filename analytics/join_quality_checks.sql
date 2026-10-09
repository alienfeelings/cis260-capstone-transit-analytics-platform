--from step 16
--prediction/schedule match rate

SELECT
    COUNT(*) AS total_predictions,
    COUNT(st.trip_id) AS matched_predictions,
    COUNT(*) - COUNT(st.trip_id) AS unmatched_predictions,

    ROUND(
        100.0 * COUNT(st.trip_id) / NULLIF(COUNT(*), 0),
        2
    ) AS match_percentage

FROM predictions AS p

LEFT JOIN stop_times AS st
    ON p.trip_id = st.trip_id
    AND p.stop_id = st.stop_id
    AND p.stop_sequence = st.stop_sequence;