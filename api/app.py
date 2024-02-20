from flask import Flask, request, jsonify
import os
from openai import OpenAI
from dotenv import load_dotenv
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

load_dotenv()

# just to debug if flask is up and running
@app.route("/")
def home():
    return "Welcome to the Flask App!"


@app.route("/chat", methods=["POST"])
def chat():
    data = request.get_json()

    # Check if 'messages' key exists in the received JSON data
    if "message" not in data:
        return jsonify({"error": "Missing 'message' in request body"}), 400

    # Extract the messages array from the request data
    user_messages = data["message"]

    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=user_messages,  # Use the user-supplied messages array
    )

    # Assuming the response structure has a 'choices' list with at least one item,
    # and each choice has a 'message' attribute. Adjust based on actual structure.
    json_response = {
        "message": [
            {
                "role": response.choices[0].message.role,
                "content": response.choices[0].message.content,
            }
        ]
    }

    # return "success"
    return jsonify(json_response)


if __name__ == "__main__":
    app.run(debug=True)
