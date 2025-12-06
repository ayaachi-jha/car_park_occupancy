-- INSERT OVERWRITE TABLE ayaachi_parking_latest_hbase_map
-- SELECT
--     t.system_code_number,
--     t.available_occupancy
-- FROM (
--     SELECT
--         system_code_number,
--         available_occupancy,
--         -- Assigns a rank based on the record timestamp (newest gets rn=1)
--         ROW_NUMBER() OVER (
--             PARTITION BY system_code_number 
--             ORDER BY record_timestamp DESC
--         ) as rn
--     FROM 
--         ayaachi_parking_avail_data
-- ) t
-- WHERE t.rn = 1;

INSERT OVERWRITE TABLE ayaachi_parking_latest_hbase_map
SELECT
    t.system_code_number,
    t.capacity,
    t.occupancy,
    t.available_occupancy,
    t.queue_length,
    t.traffic_condition_nearby,
    t.latitude,
    t.longitude
FROM (
    SELECT
        system_code_number,
        capacity,
        occupancy,
        available_occupancy,
        queue_length,
        traffic_condition_nearby,
        latitude,
        longitude,
        record_timestamp, -- Required for ORDER BY/ranking but not selected in the final output
        -- Assigns a rank of 1 to the record with the most recent timestamp 
        ROW_NUMBER() OVER (
            PARTITION BY system_code_number 
            ORDER BY record_timestamp DESC
        ) as rn
    FROM 
        ayaachi_parking_avail_data
) t
WHERE t.rn = 1;