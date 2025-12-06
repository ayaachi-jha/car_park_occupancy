CREATE EXTERNAL TABLE IF NOT EXISTS ayaachi_parking_latest_hbase_map (
  system_code_number STRING,
  available_occupancy INT
)
STORED BY 'org.apache.hadoop.hive.hbase.HBaseStorageHandler'
WITH SERDEPROPERTIES (
  "hbase.columns.mapping" = "
    :key,
    data:available_spots
  "
)
TBLPROPERTIES (
  "hbase.table.name" = "ayaachi_parking_availability_latest",
  "hbase.map.column.to.key" = "system_code_number"
);