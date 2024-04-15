""" Flask app that uses the OpenAI API to generate responses to user messages."""

import os
import certifi
import openai
from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure
from lib import chat_completion_request, create_embedding

load_dotenv()

ca = certifi.where()
URI = os.getenv("MONGODB_URI")
client = MongoClient(URI, tlsCAFile=ca)
db = client["course_db"]
collection = db["parsed_courses"]

try:
    client.admin.command("ping")
    print("Pinged your deployment. You successfully connected to MongoDB!")
except ConnectionFailure as db_error:
    print(f"Database connection error: {db_error}")

app = Flask(__name__)
CORS(app)


@app.route("/")
def home():
    """Route handler for the home page ("/"). Returns a welcome message."""
    return "Welcome to the Flask App!"


conversation_history = []


@app.route("/chat", methods=["POST"])
def chat():
    """
    Route handler for "/chat" endpoint. Receives a JSON payload with user messages,
    generates a response using the OpenAI API, and returns it as a JSON object.
    """
    data = request.get_json()

    if "message" not in data:
        return jsonify({"error": "Missing 'message' in request body"}), 400

    user_message = data["message"]
    conversation_history.append({"role": "user", "content": user_message})

    query_vector = create_embedding(user_message)

    database_response = list(
        collection.aggregate(
            [
                {
                    "$vectorSearch": {
                        "index": "parsed_courses_title_description_index",
                        "path": "embedding",
                        "queryVector": query_vector,
                        "numCandidates": 30,
                        "limit": 5,
                    }
                }
            ]
        )
    )

    recommended_courses = [
        {
            "course_code": course["course_code"],
            "title": course["title"],
            "description": course["description"],
        }
        for course in database_response
    ]

    recommendation_prompt = (
        "Here are some courses that might be relevant to your request:\n\n"
        + "\n\n".join(
            f'{course["course_code"]}: {course["title"]}\n{course["description"]}'
            for course in recommended_courses
        )
        + "\nProvide a response to the user. Incorporate this information only if relevant."
    )

    conversation_history.append({"role": "system", "content": recommendation_prompt})

    try:
        response = chat_completion_request(messages=conversation_history)
        ai_response_content = response.choices[0].message.content
        conversation_history.append(
            {"role": "assistant", "content": ai_response_content}
        )
    except openai.BadRequestError as chat_error:
        print(f"Error during chat completion request: {chat_error}")
        ai_response_content = (
            "Sorry, I encountered an error while processing your request."
        )

    return jsonify({"response": ai_response_content, "courses": recommended_courses})

if __name__ == "__main__":
    app.run(debug=True)
