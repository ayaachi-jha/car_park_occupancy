import happybase
from pyhive import hive
from geopy.geocoders import Nominatim
import json

# Imports for RAG
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
import os

CURRENT_DIRECTORY = os.getcwd()
CONFIG_PATH = os.path.join(CURRENT_DIRECTORY, "config.json")

## Get configurations
def get_configs(conf_path):
    with open(conf_path, 'r') as config_file:
        config_data = json.load(config_file)
    return config_data

config_data = get_configs(CONFIG_PATH)

HIVE_HOST_NAME = config_data.get("hive").get("host_name")
HIVE_PORT = config_data.get("hive").get("port")
HIVE_USER = config_data.get("hive").get("user")
HIVE_DATABASE = config_data.get("hive").get("database")

HBASE_HOST_NAME = config_data.get("hbase").get("host_name")
HBASE_PORT = config_data.get("hbase").get("port")

FAISS_INDEX_PATH = os.path.join(CURRENT_DIRECTORY, "faiss_index")
HIVE_SCHEMA_METADATA_PATH = os.path.join(CURRENT_DIRECTORY, "database_metadata/hive_schema.xml")


# RAG tools

embeddings_model = None
vector_db = None

def initialize_rag():
    """Initializes the RAG components."""
    global embeddings_model, vector_db
    if os.path.exists(FAISS_INDEX_PATH):
        print("Initializing RAG components...")
        embeddings_model = HuggingFaceEmbeddings(
            model_name='all-MiniLM-L6-v2',
            model_kwargs={'device': 'cpu'}
        )
        vector_db = FAISS.load_local(FAISS_INDEX_PATH, embeddings_model, allow_dangerous_deserialization=True)
        print("RAG components initialized successfully.")
    else:
        print(f"Warning: FAISS index not found at '{FAISS_INDEX_PATH}'. search_knowledge_base will not work.")

def search_knowledge_base(query: str) -> str:
    """Searches the knowledge base of text documents for relevant information."""
    global vector_db
    if vector_db is None:
        return "Error: Knowledge base not available. FAISS index not loaded."
    try:
        results = vector_db.similarity_search(query, k=3)
        if not results:
            return "No relevant information found in the knowledge base."
        context = "--- Relevant Information from Knowledge Base ---"

        for i, doc in enumerate(results):
            context += f"Source Document {i+1}:\n{doc.page_content}\n\n"
        return context
    except Exception as e:
        return f"An error occurred during knowledge base search: {e}"

def read_xml_as_text(file_path):
    """Reads an XML file and returns its content as a string."""
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            return file.read()
    except FileNotFoundError:
        return f"Error: Metadata file not found at {file_path}"
    except Exception as e:
        return f"An error occurred while reading the metadata file: {e}"

def get_relevant_tables() -> str:
    """
    Returns a string containing the schema (tables, columns, descriptions) for all available Hive tables.
    This should be the first step before writing any SQL query.
    """
    return read_xml_as_text(HIVE_SCHEMA_METADATA_PATH)


# Database and Geocoding Tools

def query_hive(query: str) -> str:
    if "delete" in query.lower() or "insert" in query.lower():
        print(f"Stopping from running delete or insert query.")
        return "You cannot run DELETE or INSERT queries. You are only allowed to run SELECT queries."

    host_name = HIVE_HOST_NAME
    port = HIVE_PORT
    user = HIVE_USER
    database = HIVE_DATABASE
    try:
        conn = hive.Connection(host=host_name, port=port, username=user, database=database)
        cursor = conn.cursor()
        cursor.execute(query)
        result = cursor.fetchall()
        return str(result)
    except Exception as e:
        return f"Error executing Hive query: {e}"
    finally:
        if 'conn' in locals() and conn: conn.close()


def query_hbase(table_name: str, row_key: str) -> str:
    host_name = HBASE_HOST_NAME
    port = HBASE_PORT
    try:
        connection = happybase.Connection(host=host_name, port=port)
        table = connection.table(table_name)
        row = table.row(row_key)
        decoded_row = {k.decode('utf-8'): v.decode('utf-8') for k, v in row.items()}
        return str(decoded_row)
    except Exception as e:
        return f"Error executing HBase query: {e}"
    finally:
        if 'connection' in locals() and connection.transport.is_open(): connection.close()

def get_location_from_longitude_latitude(longitude: float, latitude: float) -> str:
    geolocator = Nominatim(user_agent="project-birmingham-car-park-chatbot")
    location = geolocator.reverse((latitude, longitude))
    return str(location.raw) if location else "Location not found."

#### NOT USED ######

def get_hive_schema(table_name: str) -> str:
    """
    Fetches the schema for a given Hive table, including column names and data types.
    This should be the first step before constructing a query.
    :param table_name: The name of the Hive table to describe (e.g., 'ayaachi_parking_avail_data').
    """
    host_name = "localhost"
    port = 10000
    user = "hadoop"
    database = "default"

    try:
        conn = hive.Connection(host=host_name, port=port, username=user, database=database)
        cursor = conn.cursor()
        cursor.execute(f"DESCRIBE FORMATTED {table_name}")
        schema_rows = cursor.fetchall()

        col_list_start_index = next((i for i, row in enumerate(schema_rows) if row[0].strip() == '# col_name'), -1)
        if col_list_start_index != -1:
            col_list_start_index += 1
            col_list_end_index = next((i for i, row in enumerate(schema_rows[col_list_start_index:]) if row[0].strip().startswith('#')), len(schema_rows))

            formatted_schema = "Table Schema:\n"
            for row in schema_rows[col_list_start_index:col_list_start_index + col_list_end_index]:
                col_name, col_type = row[0].strip(), row[1].strip()
                if col_name:
                    formatted_schema += f"- {col_name} ({col_type})\n"
            return formatted_schema
        return "Could not parse schema."
    except Exception as e:
        return f"Error executing Hive query to get schema: {e}"
    finally:
        if 'conn' in locals() and conn: conn.close()