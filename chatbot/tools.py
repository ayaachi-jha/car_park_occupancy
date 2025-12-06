import happybase
from pyhive import hive
from geopy.geocoders import Nominatim

# Imports for RAG
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
import os

# RAG Tool

embeddings_model = None
vector_db = None
FAISS_INDEX_PATH = "faiss_index"

def initialize_rag():
    """
    Initializes the RAG components (embedding model and vector DB).
    This is called once when the application starts.
    """
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
        print(f"Warning: FAISS index not found at '{FAISS_INDEX_PATH}'. The search_knowledge_base tool will not work.")
        print("Please run 'python ingest.py' to create the index.")

def search_knowledge_base(query: str) -> str:
    """
    Searches the knowledge base of text documents for information relevant to the user's query.
    Use this for general questions about the system, its purpose, or for information not found in the databases.
    :param query: The user's query or search term.
    """
    global vector_db
    if vector_db is None:
        return "Error: The knowledge base is not available. The FAISS index has not been loaded."

    try:
        # Perform a similarity search
        results = vector_db.similarity_search(query, k=3) # Get top 3 most relevant chunks

        if not results:
            return "No relevant information found in the knowledge base."

        # Format the results into a single context string
        context = "--- Relevant Information from Knowledge Base ---"
        for i, doc in enumerate(results):
            context += f"Source Document {i+1}:\n\n"
            context += f"{doc.page_content}\n\n"
        return context
    except Exception as e:
        return f"An error occurred during the knowledge base search: {e}"


# --- Database and Geocoding Tools ---

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

def query_hive(query: str) -> str:
    host_name = "localhost"
    port = 10000
    user = "hadoop"
    database = "default"
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
    host_name = "localhost"
    port = 9090
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
