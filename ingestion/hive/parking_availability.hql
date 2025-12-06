CREATE TABLE IF NOT EXISTS parking_avail_data (
  id INT,
  system_code_number STRING,
  capacity INT,
  occupancy INT,
  available_occupancy INT,
  vehicle_type STRING,
  traffic_condition_nearby STRING,
  queue_length INT,
  is_special_day TINYINT,
  record_timestamp TIMESTAMP,
  latitude DOUBLE,
  longitude DOUBLE
)
STORED AS ORC;