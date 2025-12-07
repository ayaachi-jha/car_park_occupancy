# Car Park Occupancy Chatbot and Ingestion Pipeline

This project provides a real-time data ingestion pipeline for car park availability and a chatbot interface to query this data using natural language.

The chatbot can be used for running analytics on Hive and Hbase tables in general, thus allowing for faster and easier analytics with natural language.

## Resources
The documentation refers to the code and the paths existing in EMR. For locally referencing the code, you can see the scripts in the following directories.

- Create Table Statements are in `ingestion/hbase` and `ingestion/hiv`e directories.
- Kafka Fake Producer and Topic creation scripts are in `ingestion/kafka_ingestion`
- The Kafka Consumer Spark Streaming code is in `car_park_kafka_ingestion/` directory.
- The chatbot code is in `chatbot/` directory.



# Kappa Architecture

## 1. Data Model & Schema

The system relies on HBase & Hive to manage real-time and historical car park information.

### Hive Tables

The Hive tables provide a SQL interface to the data. The schema for these tables is dynamically fetched by the chatbot.

#### `ayaachi_parking_data` (Raw Data Table)

This table consumes the record as it is including all columns from the source. It is an external table built on top of CSV files stored in HDFS.

Reason for CSV SerDe: Since the initial data load was with CSV files. It is imperative that we adapt our big data pipeline to work with CSV in the raw table.

Create Table statement for the raw data table
```
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
```

## Batch Layer

#### `ayaachi_parking_avail_data` (Batch Layer Main Analytical Table)

This table contains detailed historical and real-time parking data. All analytical queries should primarily use this table.

It uses ORC SerDE and is a Hive managed table which allows for better performance and compression.

This table processes the data from the raw table `ayaachi_parking_data` and stores the necessary columns with the appropriate datatypes.

For ex: It removes the `id`, merges the `date` and `time` column from string to a single `Datetime` type and casts the `int` and `float` types.

*It also adds a column `available_occupancy` which specifies the available parking spots using the formula `capacity - (occupancy + queue)`*

This table is used for analytical queries on historical data.

### Create table statement
```
CREATE TABLE IF NOT EXISTS ayaachi_parking_avail_data (
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
```

The table can be updated by running this query using a cron job or a scheduler like `Oozie/Airflow` everyday.

### Updating Batch Layer Daily using HQL

```
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
```

## Speed Layer

### HBase Table

*   **`ayaachi_parking_availability_latest`**: Stores the latest, real-time data for each car park. This is the serving layer for low-latency lookups.

Create HBase table:
```
create 'ayaachi_parking_availability_latest', 'data'
```
The HBase table stores all the columns except the `record_timestamp` and the `vehicle_type` from the batch layer.

This is because the HBase table is used for low latency state query for the parking lots based on the parking lot id which is the `row_key: system_code_number`.

#### `ayaachi_parking_latest_hbase_map` (HBase Mapping Table)

This Hive table provides a SQL interface to the HBase table `ayaachi_parking_availability_latest`, allowing SQL queries on the latest data with a very low latency.

Create table statement for the HBase mapping table in Hive
```
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
```
### One-time insertion into HBase

We can use this query to rebuild our speed layer in case of failure. This query is used for initial loading of data from our batch layer - `ayaachi_parking_avail_data` table

```
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
        record_timestamp,
        ROW_NUMBER() OVER (
            PARTITION BY system_code_number
            ORDER BY record_timestamp DESC
        ) as rn
    FROM
        ayaachi_parking_avail_data
) t
WHERE t.rn = 1;
```

## 2. Spark Streaming Ingestion Pipeline

The initial loading of data is done through a `csv` file into the raw table. Once we have the initial load done we only update the batch layer table `ayaachi_parking_avail_data` using the HQL query defined in the above section.

### Kafka (Primary Source)

*Kafka Topic: `ayaachi_car_park`*

For the `HBase` real-time updates and updating the raw data table `ayaachi_parking_data` we use `Kafka` as our primary source.

Create the Kafka topic by running the script in
```/home/hadoop/ayaachi/kafka_code/create_topic.py```

Run the following -
```
cd /home/hadoop/ayaachi/kafka_code
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python create_topic.py
```

### Kappa Architecture

The ingestion pipeline uses a dual-path Spark Streaming application designed to ingest real-time JSON data from Kafka into both HBase and Hive/HDFS.

Kappa architecture is appropriate for this pipeline as the initial data load is from a CSV dataset in Kaggle and we don't have a real-time data ingestion source. So, we fake the data using a Python producer. The way the ingestion is handled with Spark is discussed below.

### 2.1 Ingestion Architecture Overview

The pipeline implements a Kappa approach, utilizing two independent streaming jobs reading from the same Kafka topic - `ayaachi_car_park` to update both the raw data table in hive - `ayaachi_parking_data` and real-time data in HBase - `ayaachi_parking_availability_latest`

#### Ingestion Paths

| Path         | Scala Class             | Target Data Store                                   | Purpose                                                                                             | Data Processing                                                              |
| :----------- | :---------------------- | :-------------------------------------------------- | :-------------------------------------------------------------------------------------------------- | :--------------------------------------------------------------------------------- |
| Speed Layer  | `CarParkHBaseIngestion`   | HBase Table (`ayaachi_parking_availability_latest`)   | Real-Time Lookups: Provides the current status of the car parking including occupancy, availability, etc. for fast application serving. | Calculates Adjusted Available Occupancy, maps JSON to HBase columns, and performs PUT operations. |
| Batch Layer  | `CarParkHiveIngestion`    | Hive External Table (`ayaachi_parking_data`)          | Historical Archive: Stores every raw JSON record as an immutable CSV file for auditing and historical analytics. | Parses raw JSON, converts to CSV format, and writes to HDFS.                       |

#### Core Calculation

The primary metric, Adjusted Available Occupancy, is calculated by the streaming job based on the current state and demand:

$$\text{Available Occupancy} = \text{Capacity} - \text{Occupancy} - \text{QueueLength}$$

### 2.2 Jar Configuration

The Uber Jar and the consumer properties file is present in
```
/home/hadoop/ayaachi/jars
```
An example `consumer.properties` file looks like this -
```
# CONFIGURATION FOR SPARK JOB
bootstrap.servers=boot-public-byg.mpcs53014kafka.2siu49.c2.kafka.us-east-1.amazonaws.com:9196

# SECURITY CONFIGURATION (From kafka.client.properties)
security.protocol=SASL_SSL
sasl.mechanism=SCRAM-SHA-512
sasl.jaas.config=org.apache.kafka.common.security.scram.ScramLoginModule required username=${SECRET}$
password=${SECRET$};
ssl.truststore.location=/usr/lib/jvm/java-11-amazon-corretto.aarch64/lib/security/cacerts
ssl.truststore.password=${SECRET}

# CONSUMER CONFIGS
group.id=ayaachi_hbase_cg
request.timeout.ms=20000
retry.backoff.ms=500
```

Consumer Groups
```
HBase Ingestion Spark Job: ayaachi_hbase_cg
Hive Ingestion Spark Job: ayaachi_hive_cg
```

### 2.3 Execution of the Spark Streaming Jobs

Both jobs must be submitted separately and run concurrently. This ensures that in case of failure of either we can separately restart it and consume the data from the last consumed offset.

 Ensure your Uber JAR (`uber-car_park_kafka_ingestion-1.0-SNAPSHOT.jar`) is built and accessible.

The Jar is present in `/home/hadoop/ayaachi/jars`

`cd /home/hadoop/ayaachi/jars`

#### Batch Ingestion

A. Start the Hive Ingestion Job (Batch Ingestion)

This job writes raw CSV files to HDFS every 5 minutes.

```bash
spark-submit --class CarParkHiveIngestion --master local[1] uber-car_park_kafka_ingestion-1.0-SNAPSHOT.jar consumer_hive.properties
```
#### Real-Time Ingestion

B. Start the HBase Ingestion Job (Speed Layer)

This job performs low-latency updates (PUTs) to the HBase table every 5 seconds.

```bash
spark-submit --class CarParkHBaseIngestion --master local[1] uber-car_park_kafka_ingestion-1.0-SNAPSHOT.jar consumer_hbase.properties
```

### 2.4 Querying and Verification

A. Speed Layer Verification (HBase)

Use the HBase Shell for the lowest latency lookup of the current state, using the `system_code_number` as the Row Key.

Test Query (HBase Shell):

```bash
hbase shell
hbase(main):001:0> get 'ayaachi_parking_availability_latest', 'BHMBCCMKT01'
```

The timestamp should tell the latest record time.

B. Batch Layer Verification (Hive/HDFS)

The Hive table (`ayaachi_parking_data`) contains all historical records, but its metadata requires maintenance since new files are added

1. HDFS Metadata Repair

The Spark job is dropping new CSV files into HDFS. Hive needs to be explicitly told to scan the directory and register these new files. If new data is not visible in Hive, run this command:

```sql
MSCK REPAIR TABLE ayaachi_parking_data;
```
This command can be run through a scheduler daily to make sure that the new data is visible.

2. Query for Latest Records in Hive

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

Expected Result: Records showing timestamps corresponding to the current time, confirming successful end-to-end ingestion.

### Mock Data Creation For Kafka
Since, the the data is from Kaggle, we only have the initial CSV file for loading the data. For further ingestion we have a mock data producer in Python which can be run with realistic values, configured by the constants defined on the top of the file.

Run the Kafka Producer -
```
cd /home/hadoop/ayaachi/kafka_code
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python fake_producer.py
```

By default it produces a record every 5 seconds until 200 records are produced.

## 3. Chatbot Application

The chatbot provides a natural language interface to query the car park data. The chatbot is not limited to querying the car park data. It has the ability to perform analytics on Hive & HBase using natural language. It answer user queries by querying the database appropriately.

### 3.1 Features

*   **Flask Backend:** A Python Flask application handles API requests and orchestrates interactions with the OpenAI model and data tools.
*   **UI:** A simple HTML/CSS/JavaScript frontend provides an interactive chat interface.
*   **Tool-Use Capabilities:** The chatbot leverages OpenAI's function calling to interact with HBase & Hive data sources.
*   **Retrieval-Augmented Generation (RAG):** Uses a local FAISS vector database to provide context from `.txt` documents, enhancing its ability to answer general questions about the system.
*   **Dynamic Schema Discovery:** Fetches live database schemas to ensure accurate SQL query generation.

### 3.2 Tools

The chatbot uses the following custom tools:

*   **`get_relevant_tables()`**: Retrieves the schema (table names, columns, descriptions) for all available Hive tables from a local XML file. This is the first step for any Hive query.
*   **`query_hive(query: str)`**: Executes a SQL query against Hive.
*   **`query_hbase(table_name: str, row_key: str)`**: Fetches real-time data for a specific car park from HBase.
*   **`search_knowledge_base(query: str)`**: Searches the RAG knowledge base for relevant information.
*   **`get_location_from_longitude_latitude(longitude: float, latitude: float)`**: Converts geographic coordinates into a physical address.

### 3.3 Setup and Running the Chatbot

#### Prerequisites

*   Python 3.10.19
*   A virtual environment.
*   An OpenAI API Key (set as `OPENAI_API_KEY` environment variable).
*   Access to your Hive and HBase services (via SSH tunnel or direct network access).

#### Installation

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/ayaachi-jha/car_park_occupancy.git
    cd car_park_occupancy
    ```
2.  **Create and activate a virtual environment:**
    ```bash
    python3.10 -m venv venv
    source venv/bin/activate
    ```
3.  **Install Python dependencies:**
    ```bash
    pip install -r chatbot/requirements.txt
    ```
4.  **Prepare RAG Knowledge Base:**
    *   Place your `.txt` documents in `chatbot/knowledge_base/`.
    *   Build the vector database:
        ```bash
        cd chatbot/
        python ingest.py
        ```
5.  **Prepare Hive Schema Metadata:**
    *   Ensure `chatbot/database_metadata/hive_schema.xml` exists and contains your table schemas.
    *   It should already exist for the car park data.

#### Running the Application

1.  **Set your OpenAI API Key:**
    ```bash
    export OPENAI_API_KEY="your_api_key_here"
    ```
2. **SSH tunnel the Hive and HBase to your local:**
    ```
    ssh -N -L 10000:localhost:10000 -L 9090:localhost:9090 hadoop@ec2-34-230-47-10.compute-1.amazonaws.com
    ```
3.  **Start the Flask server:**
    ```bash
    cd chatbot
    python app.py
    ```
4.  **Access the UI:** Open your web browser and go to `http://localhost:3030`.

### 3.4 Working of the Chatbot



---