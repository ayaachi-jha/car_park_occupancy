CREATE EXTERNAL TABLE IF NOT EXISTS ayaachi_parking_data (
  id INT,
  system_code_number STRING,
  capacity INT,
  latitude DOUBLE,
  longitude DOUBLE,
  occupancy INT,
  vehicle_type STRING,
  traffic_condition_nearby STRING,
  queue_length INT,
  is_special_day TINYINT,
  last_updated_date STRING,
  last_updated_time STRING
)
ROW FORMAT SERDE 'org.apache.hadoop.hive.serde2.OpenCSVSerde'
WITH SERDEPROPERTIES (
  "separatorChar" = ",",
  "quoteChar"     = "\"",
  "escapeChar"    = "\\"
)
STORED AS TEXTFILE
LOCATION '/ayaachi/data/'
TBLPROPERTIES ("skip.header.line.count"="1");