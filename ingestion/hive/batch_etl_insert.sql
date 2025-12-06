INSERT INTO TABLE ayaachi_parking_avail_data
SELECT
    t1.id,
    t1.system_code_number,
    t1.capacity,
    t1.occupancy,
    (t1.capacity - t1.occupancy - t1.queue_length) AS available_occupancy,
    t1.vehicle_type,
    t1.traffic_condition_nearby,
    t1.queue_length,
    t1.is_special_day,
    from_unixtime(
        unix_timestamp(
            CONCAT(t1.last_updated_date, ' ', t1.last_updated_time),
            'dd-MM-yyyy HH:mm:ss'
        )
    ) AS record_timestamp,
    t1.latitude,
    t1.longitude
FROM
    ayaachi_parking_data t1;