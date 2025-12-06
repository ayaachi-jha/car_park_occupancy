
import os
import json
import logging
from flask import Flask, request, jsonify, send_from_directory
from openai import OpenAI

# Import the AI configurations and tools
from tool_conf import TOOL_LIST, AVAILABLE_FUNCTIONS
from prompts import SYSTEM_PROMPT
from tools import initialize_rag
from ingest import create_vector_db

MODEL = "gpt-3.5-turbo"

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

app = Flask(__name__, static_folder='public')

# Init OpenAI client
client = OpenAI(
    api_key=os.environ.get("OPENAI_API_KEY"),
)

# A dictionary to map tool names to actual functions
available_functions = AVAILABLE_FUNCTIONS

# Chat handling
def handle_chat_interaction(messages):
    """
    Handles the main chat interaction loop with the OpenAI model,
    including tool calls.
    """
    # Loop until the model gives a final answer ('stop')
    while True:
        response = client.chat.completions.create(
            model=MODEL,
            messages=messages,
            tools=TOOL_LIST,
            tool_choice="auto",
        )

        choice = response.choices[0]
        response_message = choice.message
        messages.append(response_message)  # Append the response to history

        # If the model wants to call tools, handle them
        if choice.finish_reason == 'tool_calls':
            for tool_call in response_message.tool_calls:
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
            # Go back to the start of the loop to let the model process the tool results
            continue

        # If the model is done, break the loop
        elif choice.finish_reason == 'stop':
            break

        else:
            logging.warning(f"Unexpected finish reason: {choice.finish_reason}")
            break

    # The last message in the history is the final reply
    return messages[-1]

# --- Flask Web Routes ---
@app.route('/')
def index():
    return send_from_directory('public', 'index.html')

@app.route('/<path:path>')
def serve_static(path):
    return send_from_directory('public', path)

@app.route('/api/chat', methods=['POST'])
def chat():
    """
    The main web endpoint for handling chat requests.
    """
    try:
        data = request.get_json()
        messages = data['messages']

        # Add the system prompt on the first conversation
        if len(messages) == 1:
            messages.insert(0, {"role": "system", "content": SYSTEM_PROMPT})

        # Call chat handler
        final_reply = handle_chat_interaction(messages)

        return jsonify({'reply': final_reply.to_dict()})

    except Exception as e:
        logging.error(f"An error occurred: {e}", exc_info=True)
        return jsonify({'error': 'Error processing your request'}), 500

if __name__ == '__main__':
    # Initialize the RAG system on startup
    create_vector_db()
    initialize_rag()
    # RUN ITTTT!!!!!
    app.run(host='0.0.0.0', port=3030, debug=True)
