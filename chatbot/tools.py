
import happybase
from pyhive import hive

def query_hive(query: str) -> str:
    """
    Executes a read-only SQL query on a Hive table and returns the result.
    :param query: The SQL query to execute.
    """
    # TODO: Replace with your EMR master node's hostname or IP.
    host_name = "localhost"
    port = 10000

    # TODO: Update with your username and database if needed.
    user = "hadoop"
    database = "default"

    try:
        # Establish connection to Hive
        conn = hive.Connection(host=host_name, port=port, username=user, database=database)
        cursor = conn.cursor()

        # Execute the query
        cursor.execute(query)

        # Fetch and format results
        result = cursor.fetchall()
        conn.close()

        # Convert list of tuples to a string format for the LLM
        return str(result)
    except Exception as e:
        return f"Error executing Hive query: {e}"

def query_hbase(table_name: str, row_key: str) -> str:
    """
    Fetches a single row from an HBase table based on its row key.
    :param table_name: The name of the HBase table.
    :param row_key: The row key to fetch.
    """
    # TODO: Replace with your HBase Thrift server's hostname or IP.
    # This might be your EMR master node.
    host_name = "localhost"
    port = 9090

    try:
        # Establish connection to HBase
        connection = happybase.Connection(host=host_name, port=port)
        table = connection.table(table_name)

        # Fetch the row
        row = table.row(row_key)

        connection.close()

        # Decode bytes to string for JSON serialization
        decoded_row = {k.decode('utf-8'): v.decode('utf-8') for k, v in row.items()}

        return str(decoded_row)
    except Exception as e:
        return f"Error executing HBase query: {e}"

# Example usage (for testing purposes)
if __name__ == '__main__':
    # pass
    print("This file contains tool definitions for querying Hive and HBase.")
    print("It is not meant to be run directly in production, but for import.")

    # print("Testing Hive query...")
    # hive_result = query_hive("SELECT * FROM ayaachi_parking_data LIMIT 5")
    # print(f"Hive Result: {hive_result}")

    # print("\nTesting HBase query...")
    # hbase_result = query_hbase("ayaachi_parking_availability_latest", "BHMBCCMKT01")
    # print(f"HBase Result: {hbase_result}")

