import happybase
from pyhive import hive
from geopy.geocoders import Nominatim

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
        
        # Execute DESCRIBE FORMATTED to get detailed schema
        cursor.execute(f"DESCRIBE FORMATTED {table_name}")
        
        # Fetch all rows and format them into a single string
        schema_rows = cursor.fetchall()
        
        # Find the start of the column list
        col_list_start_index = -1
        for i, row in enumerate(schema_rows):
            if row[0].strip() == '# col_name':
                col_list_start_index = i + 1
                break
        
        # Find the end of the column list
        col_list_end_index = -1
        if col_list_start_index != -1:
            for i in range(col_list_start_index, len(schema_rows)):
                if schema_rows[i][0].strip().startswith('#'):
                    col_list_end_index = i
                    break
            if col_list_end_index == -1:
                col_list_end_index = len(schema_rows)

        # Format the relevant part of the schema
        if col_list_start_index != -1:
            formatted_schema = "Table Schema:\n"
            for row in schema_rows[col_list_start_index:col_list_end_index]:
                col_name = row[0].strip()
                col_type = row[1].strip()
                if col_name: # Avoid empty lines
                    formatted_schema += f"- {col_name} ({col_type})\n"
            return formatted_schema
        else:
            return "Could not parse schema from DESCRIBE FORMATTED output."

    except Exception as e:
        return f"Error executing Hive query to get schema: {e}"
    finally:
        if 'conn' in locals() and conn:
            conn.close()


def query_hive(query: str) -> str:
    """
    Executes a read-only SQL query on a Hive table and returns the result.
    :param query: The SQL query to execute.
    """
    host_name = "localhost"
    port = 10000
    user = "hadoop"
    database = "default"

    try:
        conn = hive.Connection(host=host_name, port=port, username=user, database=database)
        cursor = conn.cursor()
        cursor.execute(query)
        result = cursor.fetchall()
        conn.close()

        return str(result)
    except Exception as e:
        return f"Error executing Hive query: {e}"

def query_hbase(table_name: str, row_key: str) -> str:
    """
    Fetches a single row from an HBase table based on its row key.
    :param table_name: The name of the HBase table.
    :param row_key: The row key to fetch.
    """
    host_name = "localhost"
    port = 9090

    try:
        connection = happybase.Connection(host=host_name, port=port)
        table = connection.table(table_name)
        row = table.row(row_key)
        connection.close()

        decoded_row = {k.decode('utf-8'): v.decode('utf-8') for k, v in row.items()}

        return str(decoded_row)
    except Exception as e:
        return f"Error executing HBase query: {e}"

def get_location_from_longitude_latitude(longitude: float, latitude: float) -> str:
    """
    Returns the location of the place from the longitude and the latitude

    :param longitude: Longitude coordinates
    :param latitude: Latitude coordinates
    """
    # Init the Nominatim geocoder
    # unique user_agent string
    geolocator = Nominatim(user_agent="project-birmingham-car-park-chatbot")

    # Perform reverse geocoding
    location = geolocator.reverse((latitude, longitude))

    # Print the full address
    if location:
        print(f"Address: {location.address}")
        print(f"Raw location data: {location.raw}")
        return str(location.raw)
    else:
        print("Could not find location for the provided coordinates.")
        return "Location not found."

if __name__ == '__main__':
    print("This file contains tool definitions.")
    print("\nTesting get_hive_schema...")
    schema_result = get_hive_schema("ayaachi_parking_avail_data")
    print(f"Schema Result:\n{schema_result}")
    
    # print("\nTesting Hive query...")
    # hive_result = query_hive("SELECT * FROM ayaachi_parking_avail_data LIMIT 1")
    # print(f"Hive Result: {hive_result}")