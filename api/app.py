"""Flask app that uses the OpenAI API to generate responses to user messages."""
import os
from flask import Flask, request, jsonify
from openai import OpenAI
from dotenv import load_dotenv
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

load_dotenv()

@app.route("/")
def home():
    """
    This function is the route handler for the home page ("/").
    It returns a welcome message when the Flask app is started successfully.
    """
    return "Welcome to the Flask App!"

conversation_history = []

@app.route("/chat", methods=["POST"])
def chat():
    """
    This function is the route handler for the "/chat" endpoint.
    It receives a JSON payload containing user messages and uses 
    the OpenAI API to generate a response.
    The response is then returned as a JSON object.
    """
    data = request.get_json()

    if "message" not in data:
        return jsonify({"error": "Missing 'message' in request body"}), 400

    user_message = data["message"]
    conversation_history.append({"role": "user", "content": user_message})

    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=conversation_history,
    )

    ai_response_content = response.choices[0].message.content
    conversation_history.append({"role": "assistant", "content": ai_response_content})

    return jsonify({"message": ai_response_content})

if __name__ == "__main__":
    app.run(debug=True)
