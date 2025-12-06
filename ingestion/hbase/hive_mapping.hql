CREATE EXTERNAL TABLE IF NOT EXISTS ayaachi_parking_latest_hbase_map (
  system_code_number STRING,
  capacity INT,
  occupancy INT,
  available_occupancy INT,
  queue_length INT,
  traffic_condition_nearby STRING,
  latitude DOUBLE,
  longitude DOUBLE
)
STORED BY 'org.apache.hadoop.hive.hbase.HBaseStorageHandler'
WITH SERDEPROPERTIES (
  "hbase.columns.mapping" = "
    :key,
    data:capacity,
    data:occupancy,
    data:available_occupancy,
    data:queue_length,
    data:traffic_condition,
    data:latitude,
    data:longitude
  "
)
TBLPROPERTIES (
  "hbase.table.name" = "ayaachi_parking_availability_latest",
  "hbase.map.column.to.key" = "system_code_number"
);