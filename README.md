# Car Park Occupancy Chatbot and Ingestion Pipeline

This project provides a real-time data ingestion pipeline for car park availability and a chatbot interface to query this data using natural language.

## 1. Data Model & Schema

The system relies on several data stores to manage real-time and historical car park information.

### HBase Table

*   **`ayaachi_parking_availability_latest`**: Stores the absolute latest, real-time data for each car park. This is the serving layer for low-latency lookups.

### Hive Tables

The Hive tables provide a SQL interface to the data. The schema for these tables is dynamically fetched by the chatbot.

#### `ayaachi_parking_avail_data` (Main Analytical Table)

This table contains detailed historical and real-time parking data. All analytical queries should primarily use this table.

```xml
<table name="ayaachi_parking_avail_data" description="Contains historical and real-time parking data. All analytical queries should use this table.">
  <columns>
    <column><name>id</name><type>INT</type><description>A unique ID for each data record.</description></column>
    <column><name>system_code_number</name><type>STRING</type><description>The unique identifier for the car park.</description></column>
    <column><name>capacity</name><type>INT</type><description>The total number of parking spaces in the car park.</description></column>
    <column><name>occupancy</name><type>INT</type><description>The number of spaces that were occupied at the time of the record.</description></column>
    <column><name>available_occupancy</name><type>INT</type><description>The number of spaces that were available at the time of the record.</description></column>
    <column><name>vehicle_type</name><type>STRING</type><description>The type of vehicle associated with the record.</description></column>
    <column><name>traffic_condition_nearby</name><type>STRING</type><description>A description of the traffic status near the car park (e.g., 'heavy', 'light').</description></column>
    <column><name>queue_length</name><type>INT</type><description>The number of vehicles waiting to enter the car park at the time of the record.</description></column>
    <column><name>is_special_day</type><type>TINYINT</type><description>A flag (1 for true, 0 for false) indicating if the record is from a special day or event.</description></column>
    <column><name>record_timestamp</name><type>TIMESTAMP</type><description>The exact date and time of the data record.</description></column>
    <column><name>latitude</name><type>DOUBLE</type><description>The geographic latitude of the car park.</description></column>
    <column><name>longitude</name><type>DOUBLE</type><description>The geographic longitude of the car park.</description></column>
  </columns>
</table>
```

#### `ayaachi_parking_latest_hbase_map` (HBase Mapping Table)

This Hive table provides a SQL interface to the HBase table, allowing SQL queries on the latest data.

```xml
<table name="ayaachi_parking_latest_hbase_map" description="A real-time view of the latest data for all car parks, mapped from HBase.">
  <columns>
    <column><name>system_code_number</name><type>STRING</type><description>The unique identifier for the car park. This is the primary key.</description></column>
    <column><name>capacity</name><type>INT</type><description>The total number of parking spaces in the car park.</description></column>
    <column><name>occupancy</name><type>INT</type><description>The number of spaces that are currently occupied.</description></column>
    <column><name>available_occupancy</type><type>INT</type><description>The number of spaces that are currently available.</description></column>
    <column><name>queue_length</name><type>INT</type><description>The number of vehicles currently waiting to enter the car park.</description></column>
    <column><name>traffic_condition_nearby</name><type>STRING</type><description>A description of the current traffic status near the car park (e.g., 'heavy', 'light').</description></column>
    <column><name>latitude</name><type>DOUBLE</type><description>The geographic latitude of the car park.</description></column>
    <column><name>longitude</name><type>DOUBLE</type><description>The geographic longitude of the car park.</description></column>
  </columns>
</table>
```

## 2. 🅿️ Spark Streaming Ingestion Pipeline

This section outlines the architecture, configuration, and operation of the dual-path Spark Streaming application designed to ingest real-time JSON data from Kafka into both HBase and Hive/HDFS.

### 2.1 Architectural Overview

The pipeline implements a Lambda/Kappa-inspired approach, utilizing two independent streaming jobs reading from the same Kafka topic to fulfill distinct latency requirements.

#### Ingestion Paths

| Path         | Scala Class             | Target Data Store                                   | Purpose                                                                                             | Update Frequency      |
| :----------- | :---------------------- | :-------------------------------------------------- | :-------------------------------------------------------------------------------------------------- | :-------------------- |
| Speed Layer  | `CarParkHBaseIngestion`   | HBase Table (`ayaachi_parking_availability_latest`)   | Real-Time Lookups: Provides the current, calculated, queue-adjusted occupancy for fast application serving. | Low Latency (~5 seconds) |
| Batch Layer  | `CarParkHiveIngestion`    | Hive External Table (`ayaachi_parking_data`)          | Historical Archive: Stores every raw JSON record as an immutable CSV file for auditing and historical analytics. | Batch Interval (30 seconds) |

#### Core Calculation

The primary metric, Adjusted Available Occupancy, is calculated by the streaming job based on the current state and demand:

$$\text{Available Occupancy} = \text{Capacity} - \text{Occupancy} - \text{QueueLength}$$

### 2.2 Kafka Security Configuration

The application uses Spark Streaming (DStreams) and relies on external configuration to establish a secure connection via SASL/SSL. The following parameters are required to be present in the `consumer.properties` file that is passed as the first command-line argument (`args(0)`) to both Spark applications:

| Property                | Description                                          | Status                       |
| :---------------------- | :--------------------------------------------------- | :--------------------------- |
| `bootstrap.servers`     | Broker Endpoint (e.g., `boot-public-byg...:9196`). | Required for network access. |
| `security.protocol`     | `SASL_SSL`                                           | Enables encryption and authentication. |
| `sasl.mechanism`        | `SCRAM-SHA-512`                                      | Specific authentication method. |
| `sasl.jaas.config`      | Credentials (`username='mpcs53014-2025'`, etc.).    | Provides SASL login details. |
| `ssl.truststore.location` | Path to your Java `cacerts` file.                    | Required for the SSL handshake. |
| `group.id`              | Consumer group ID for offset management.             | Required for consumer tracking. |

### 2.3 Execution Commands

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

### 2.4 Querying and Maintenance

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

2. Query for Latest Records (Corrected Ordering)

Since your date columns are stored as strings (DD-MM-YYYY), we must cast them to a numeric timestamp for correct ordering, ensuring we see the most recent data written by the streaming job.

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

## 3. Chatbot Application

The chatbot provides a natural language interface to query the car park data.

### 3.1 Features

*   **Flask Backend:** A Python Flask application handles API requests and orchestrates interactions with the OpenAI model and data tools.
*   **Dynamic UI:** A simple HTML/CSS/JavaScript frontend provides an interactive chat interface.
*   **Tool-Use Capabilities:** The chatbot leverages OpenAI's function calling to interact with various data sources and services.
*   **Retrieval-Augmented Generation (RAG):** Uses a local FAISS vector database to provide context from `.txt` documents, enhancing its ability to answer general questions about the system.
*   **Context Management:** Maintains conversation history and can summarize it to stay within token limits (though this feature is currently disabled).
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

*   Python 3.10.19 (recommended, installed via `pyenv` or system-wide `altinstall`).
*   A virtual environment.
*   An OpenAI API Key (set as `OPENAI_API_KEY` environment variable).
*   Access to your Hive and HBase services (via SSH tunnel or direct network access).

#### Installation

1.  **Clone the repository:**
    ```bash
    git clone <repository_url>
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
        python chatbot/ingest.py
        ```
5.  **Prepare Hive Schema Metadata:**
    *   Ensure `chatbot/database_metadata/hive_schema.xml` exists and contains your table schemas.

#### Running the Application

1.  **Set your OpenAI API Key:**
    ```bash
    export OPENAI_API_KEY="your_api_key_here"
    ```
2.  **Start the Flask server:**
    ```bash
    python chatbot/app.py
    ```
3.  **Access the UI:** Open your web browser and go to `http://localhost:3030`.

### 3.4 Deployment to EC2

When deploying to an EC2 instance (separate from your EMR master node):

1.  **Python Environment:** Ensure Python 3.10.19 and all dependencies are installed in a virtual environment.
2.  **HBase/Hive Hostname:** **CRITICAL:** In `chatbot/tools.py`, change all instances of `host_name = "localhost"` to the **private IP address** of your EMR master node (e.g., `172.31.91.77`).
3.  **RAG Index:** Copy the `chatbot/knowledge_base/` and `chatbot/faiss_index/` directories to the EC2 instance.
4.  **Schema XML:** Copy `chatbot/database_metadata/hive_schema.xml` to the EC2 instance.
5.  **Security Groups:** Ensure the EMR master node's security group allows inbound TCP traffic on Hive (port 10000) and HBase Thrift (port 8070) from the security group of your application's EC2 instance.

---