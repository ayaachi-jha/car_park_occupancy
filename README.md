# car_park_occupancy
A chatbot for suggesting open car parkings available in the city of Birmingham

## Car Park Streaming Ingestion Pipeline

This document outlines the architecture, configuration, and operation of the dual-path Spark Streaming application designed to ingest real-time JSON data from Kafka into both a high-speed Serving Layer (HBase) and a historical Batch Layer (Hive/HDFS).

### 1. Architectural Overview

The pipeline implements a Lambda/Kappa-inspired approach, utilizing two independent streaming jobs reading from the same Kafka topic to fulfill distinct latency requirements.

### 1.1 Ingestion Paths

| Path         | Scala Class             | Target Data Store                                   | Purpose                                                                                             | Update Frequency      |
| :----------- | :---------------------- | :-------------------------------------------------- | :-------------------------------------------------------------------------------------------------- | :-------------------- |
| Speed Layer  | CarParkHBaseIngestion   | HBase Table (ayaachi_parking_availability_latest)   | Real-Time Lookups: Provides the current, calculated, queue-adjusted occupancy for fast application serving. | Low Latency (~5 seconds) |
| Batch Layer  | CarParkHiveIngestion    | Hive External Table (ayaachi_parking_data)          | Historical Archive: Stores every raw JSON record as an immutable CSV file for auditing and historical analytics. | Batch Interval (30 seconds) |

### 1.2 Core Calculation

The primary metric, Adjusted Available Occupancy, is calculated by the streaming job based on the current state and demand:

$$\text{Available Occupancy} = \text{Capacity} - \text{Occupancy} - \text{QueueLength}$$

### 2. Configuration and Security

The application uses Spark Streaming (DStreams) and relies on external configuration to establish a secure connection via SASL/SSL.

2.1 Kafka Security Configuration

| Property                | Description                                          | Status                       |
| :---------------------- | :--------------------------------------------------- | :--------------------------- |
| `bootstrap.servers`     | Broker Endpoint (e.g., `boot-public-byg...:9196`). | Required for network access. |
| `security.protocol`     | `SASL_SSL`                                           | Enables encryption and authentication. |
| `sasl.mechanism`        | `SCRAM-SHA-512`                                      | Specific authentication method. |
| `sasl.jaas.config`      | Credentials (`username='mpcs53014-2025'`, etc.).    | Provides SASL login details. |
| `ssl.truststore.location` | Path to your Java `cacerts` file.                    | Required for the SSL handshake. |
| `group.id`              | Consumer group ID for offset management.             | Required for consumer tracking. |

### 3. Execution Commands

Both jobs must be submitted separately and run concurrently. Ensure your Uber JAR (`uber-car_park_kafka_ingestion-1.0-SNAPSHOT.jar`) is built and accessible.

A. Start the Hive Ingestion Job (Batch Archive)

This job writes raw CSV files to HDFS every 5 minutes (or 30 seconds, per the code's configuration).

```bash
spark-submit \
  --class "CarParkHiveIngestion" \
  --master yarn \
  --deploy-mode cluster \
  /path/to/your/uber-car_park_kafka_ingestion-1.0-SNAPSHOT.jar \
  /path/to/config/consumer.properties
```

B. Start the HBase Ingestion Job (Speed Layer)

This job performs low-latency updates (PUTs) to the HBase table every 5 seconds.

```bash
spark-submit \
  --class "CarParkHBaseIngestion" \
  --master yarn \
  --deploy-mode cluster \
  /path/to/your/uber-car_park_kafka_ingestion-1.0-SNAPSHOT.jar \
  /path/to/config/consumer.properties
```

### 4. Querying and Maintenance

A. Speed Layer Verification (HBase)

Use the HBase Shell for the lowest latency lookup of the current state, using the `system_code_number` as the Row Key.

Test Query (HBase Shell):

```bash
hbase shell
hbase(main):001:0> get 'ayaachi_parking_availability_latest', 'BHMBCCMKT01'
```

Expected Result: The latest calculated `available_occupancy`, `capacity`, and `queue_length` for that specific lot.

B. Batch Layer Verification (Hive/HDFS)

The Hive table (`ayaachi_parking_data`) contains all historical records, but its metadata requires maintenance.

1. HDFS Metadata Repair (CRITICAL MAINTENANCE)

The Spark job is dropping new CSV files into HDFS. Hive needs to be explicitly told to scan the directory and register these new files. If new data is not visible in Hive, run this command:

```sql
MSCK REPAIR TABLE ayaachi_parking_data;
```

### 2. Query for Latest Records (Corrected Ordering)

Since date columns are stored as strings (DD-MM-YYYY), we must cast them to a numeric timestamp for correct ordering, ensuring we see the most recent data written by the streaming job.

Test Query (Hive/Spark SQL):

```sql
SELECT
    system_code_number,
    occupancy,
    capacity,
    last_updated_date,
    last_updated_time
FROM
    ayaachi_parking_data
ORDER BY
    UNIX_TIMESTAMP(
        CONCAT(last_updated_date, ' ', last_updated_time),
        'dd-MM-yyyy HH:mm:ss'
    ) DESC
LIMIT 10;
```

Expected Result: Records showing timestamps corresponding to the current time, confirming successful end-to-end ingestion and sorting.
