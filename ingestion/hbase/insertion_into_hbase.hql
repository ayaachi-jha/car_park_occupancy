INSERT OVERWRITE TABLE ayaachi_parking_latest_hbase_map
SELECT
    t.system_code_number,
    t.available_occupancy
FROM (
    SELECT
        system_code_number,
        available_occupancy,
        -- Assigns a rank based on the record timestamp (newest gets rn=1)
        ROW_NUMBER() OVER (
            PARTITION BY system_code_number 
            ORDER BY record_timestamp DESC
        ) as rn
    FROM 
        ayaachi_parking_avail_data
) t
WHERE t.rn = 1;