import os
import json
import logging
from flask import Flask, request, jsonify, send_from_directory
from openai import OpenAI

# Import the AI configurations
from tool_conf import TOOL_LIST, AVAILABLE_FUNCTIONS
from prompts import SYSTEM_PROMPT

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

app = Flask(__name__, static_folder='public')

# Init OpenAI client
client = OpenAI(
    api_key=os.environ.get("OPENAI_API_KEY"),
)

# Define the tools for the OpenAI API
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
        # Expect a 'messages' list from the frontend
        messages = data['messages']

        # Add the system prompt if it's the first message
        if len(messages) == 1:
            messages.insert(0, {"role": "system", "content": SYSTEM_PROMPT})

        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=messages,
            tools=tools,
            tool_choice="auto",
        )

        response_message = response.choices[0].message
        tool_calls = response_message.tool_calls

        # This loop enables the multi-step tool calling
        while tool_calls:
            messages.append(response_message)
            for tool_call in tool_calls:
                function_name = tool_call.function.name
                logging.info(f"Model requested to call function: {function_name}")
                function_to_call = available_functions[function_name]
                function_args = json.loads(tool_call.function.arguments)
                function_response = function_to_call(**function_args)
                messages.append(
                    {
                        "tool_call_id": tool_call.id,
                        "role": "tool",
                        "name": function_name,
                        "content": function_response,
                    }
                )
            
            # Make the next call to see what the model does next
            second_response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=messages,
                tools=tools,
                tool_choice="auto",
            )
            response_message = second_response.choices[0].message
            tool_calls = response_message.tool_calls

        # The final reply from the assistant
        reply_message = response_message.to_dict()

        return jsonify({'reply': reply_message})

    except Exception as e:
        logging.error(f"An error occurred: {e}", exc_info=True)
        return jsonify({'error': 'Error processing your request'}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=3030, debug=True)