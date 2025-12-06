from tools import (
    query_hive, 
    query_hbase, 
    get_location_from_longitude_latitude, 
    search_knowledge_base,
    get_relevant_tables
)

TOOL_LIST = [
    {
        "type": "function",
        "function": {
            "name": "get_relevant_tables",
            "description": "Call this first to get the schemas of all available Hive tables before writing a SQL query. It provides table names, column names, data types, and descriptions.",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "query_hive",
            "description": "Executes a read-only SQL query on a Hive table, based on a schema you have already fetched.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The SQL query to execute.",
                    },
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "search_knowledge_base",
            "description": "Searches text documents for general information about the system or its purpose.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The user's question or search term.",
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
            "description": "Fetches real-time data for a specific car park from HBase using its row key.",
            "parameters": {
                "type": "object",
                "properties": {
                    "table_name": {
                        "type": "string",
                        "description": "The name of the HBase table, e.g., 'ayaachi_parking_availability_latest'",
                    },
                    "row_key": {
                        "type": "string",
                        "description": "The row key (system_code_number) to fetch.",
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
            "description": "Gets a physical address from longitude and latitude coordinates.",
            "parameters": {
                "type": "object",
                "properties": {
                    "longitude": {"type": "number"},
                    "latitude": {"type": "number"},
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
    "search_knowledge_base": search_knowledge_base,
    "get_relevant_tables": get_relevant_tables,
}