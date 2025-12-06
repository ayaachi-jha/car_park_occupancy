from tools import query_hive, query_hbase, get_location_from_longitude_latitude, get_hive_schema

TOOL_LIST = [
    {
        "type": "function",
        "function": {
            "name": "get_hive_schema",
            "description": "Use this tool first to get the schema of a Hive table before you write a SQL query. This is a mandatory first step.",
            "parameters": {
                "type": "object",
                "properties": {
                    "table_name": {
                        "type": "string",
                        "description": "The name of the Hive table to describe, e.g., 'ayaachi_parking_avail_data'",
                    },
                },
                "required": ["table_name"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "query_hive",
            "description": "Executes a read-only SQL query on a Hive table to find information about car park data.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The SQL query to execute. Should be a SELECT statement based on a schema you have already fetched.",
                    },
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "query_hbase",
            "description": "Fetches real-time availability for a specific car park from an HBase table using its row key (system_code_number).",
            "parameters": {
                "type": "object",
                "properties": {
                    "table_name": {
                        "type": "string",
                        "description": "The name of the HBase table, e.g., 'ayaachi_parking_availability_latest'",
                    },
                    "row_key": {
                        "type": "string",
                        "description": "The row key to fetch, which corresponds to the car park's system_code_number, e.g., 'BHMBCCMKT01'",
                    },
                },
                "required": ["table_name", "row_key"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_location_from_longitude_latitude",
            "description": "Gives the location of a place from the longitude and the latitude. Use it when you know the longitude and latitude of the place.",
            "parameters": {
                "type": "object",
                "properties": {
                    "longitude": {
                        "type": "number",
                        "description": "The longitude of the address of the location which is needed.",
                    },
                    "latitude": {
                        "type": "number",
                        "description": "The latitude of the address of the location which is needed.",
                    },
                },
                "required": ["longitude", "latitude"],
            },
        },
    },
]

AVAILABLE_FUNCTIONS = {
    "query_hive": query_hive,
    "query_hbase": query_hbase,
    "get_location_from_longitude_latitude": get_location_from_longitude_latitude,
    "get_hive_schema": get_hive_schema,
}