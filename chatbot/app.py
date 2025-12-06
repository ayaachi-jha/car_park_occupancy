
import os
from flask import Flask, request, jsonify, send_from_directory
from openai import OpenAI

app = Flask(__name__, static_folder='public')

client = OpenAI(
    api_key=os.environ.get("OPENAI_API_KEY"),
)

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
        message = data['message']

        chat_completion = client.chat.completions.create(
            messages=[
                {
                    "role": "user",
                    "content": message,
                }
            ],
            model="gpt-3.5-turbo",
        )

        reply = chat_completion.choices[0].message.content
        return jsonify({'reply': reply})

    except Exception as e:
        print(f"Error: {e}")
        return jsonify({'error': 'Error processing your request'}), 500

if __name__ == '__main__':
    app.run(port=3000, debug=True)
