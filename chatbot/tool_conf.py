from tools import query_hive, query_hbase

TOOL_LIST = [
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
                        "description": "The SQL query to execute. Should be a SELECT statement.",
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
            "description": "Fetches real-time availability for a specific car park from an HBase table using its row key (SystemCode).",
            "parameters": {
                "type": "object",
                "properties": {
                    "table_name": {
                        "type": "string",
                        "description": "The name of the HBase table, e.g., 'ayaachi_parking_availability_latest'",
                    },
                    "row_key": {
                        "type": "string",
                        "description": "The row key to fetch, which corresponds to the car park's SystemCode, e.g., 'BHMBCCMKT01'",
                    },
                },
                "required": ["table_name", "row_key"],
            },
        },
    }
]

AVAILABLE_FUNCTIONS = {
    "query_hive": query_hive,
    "query_hbase": query_hbase,
}