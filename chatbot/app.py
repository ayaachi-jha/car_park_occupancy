import os
import json
import logging
from flask import Flask, request, jsonify, send_from_directory
from openai import OpenAI

# Import the tool functions
# from tools import query_hive, query_hbase
from tool_conf import TOOL_LIST, AVAILABLE_FUNCTIONS

app = Flask(__name__, static_folder='public')

# Initialize the OpenAI client
client = OpenAI(
    api_key=os.environ.get("OPENAI_API_KEY"),
)

# Define the tools for the OpenAI API
# The function descriptions are crucial for the model to understand how to use them.
tools = TOOL_LIST

# A dictionary to map tool names to actual functions
available_functions = AVAILABLE_FUNCTIONS

@app.route('/')
def index():
    return send_from_directory('public', 'index.html')

@app.route('/<path:path>')
def serve_static(path):
    return send_from_directory('public', path)

@app.route('/api/chat', methods=['POST'])
def chat():
    try:
        data = request.get_json()
        user_message = data['message']

        # We need to maintain a list of messages for context
        messages = [{"role": "user", "content": user_message}]

        # First API call to see if the model wants to use a tool
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=messages,
            tools=tools,
            tool_choice="auto",
        )

        response_message = response.choices[0].message
        tool_calls = response_message.tool_calls

        # Check if the model wants to call a tool
        if tool_calls:
            messages.append(response_message)  # Append the assistant's reply

            # Execute all tool calls
            for tool_call in tool_calls:
                # logging.info(f"Tool call: {tool_call.function_name}")

                function_name = tool_call.function.name
                function_to_call = available_functions[function_name]
                function_args = json.loads(tool_call.function.arguments)

                # Call the actual function with the arguments
                function_response = function_to_call(**function_args)

                # Append the tool's response to the message history
                messages.append(
                    {
                        "tool_call_id": tool_call.id,
                        "role": "tool",
                        "name": function_name,
                        "content": function_response,
                    }
                )

            # Second API call to get a natural language response from the model
            second_response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=messages,
            )
            reply = second_response.choices[0].message.content
        else:
            # If no tool is called, just return the model's direct response
            reply = response_message.content

        return jsonify({'reply': reply})

    except Exception as e:
        print(f"Error: {e}")
        return jsonify({'error': 'Error processing your request'}), 500

if __name__ == '__main__':
    app.run(port=3000, debug=True)