from tools import (
    query_hive, 
    query_hbase, 
    get_location_from_longitude_latitude, 
    get_hive_schema,
    search_knowledge_base
)

TOOL_LIST = [
    {
        "type": "function",
        "function": {
            "name": "search_knowledge_base",
            "description": "Searches a knowledge base of text documents for information. Use this for general questions about the system, its purpose, or for information not found in the databases.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The user's question or search term to look for in the documents.",
                    },
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_hive_schema",
            "description": "Use this tool to get the schema of a Hive table before you write a SQL query.",
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
            "description": "Executes a read-only SQL query on a Hive table.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The SQL query to execute, based on a schema you have already fetched.",
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
            "description": "Fetches real-time data for a specific car park from an HBase table using its row key.",
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
    "get_hive_schema": get_hive_schema,
    "search_knowledge_base": search_knowledge_base,
}
