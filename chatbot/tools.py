import happybase
from pyhive import hive

from geopy.geocoders import Nominatim

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
        # You can access more specific details from location.raw if needed
        # print(f"Raw data: {location.raw}")
        return str(location.raw)
    else:
        print("Could not find location for the provided coordinates.")



if __name__ == '__main__':
    # pass
    print("This file contains tool definitions for querying Hive and HBase.")

    print("Testing Hive query...")
    hive_result = query_hive("SELECT * FROM ayaachi_parking_avail_data LIMIT 5")
    print(f"Hive Result: {hive_result}")

    print("\nTesting HBase query...")
    hbase_result = query_hbase("ayaachi_parking_availability_latest", "BHMBCCMKT01")
    print(f"HBase Result: {hbase_result}")

