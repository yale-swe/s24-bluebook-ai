from urllib.parse import urljoin
from flask import Flask, request, jsonify, session, redirect, url_for
from flask_cors import CORS
from flask_cas import CAS, login_required
import os
from dotenv import load_dotenv
from lib import chat_completion_request, create_embedding, tools
import json
from pymongo.mongo_client import MongoClient
import requests
import xml.etree.ElementTree as ET
import datetime
from uuid import uuid4

COURSE_QUERY_LIMIT = 5
SAFETY_CHECK_ENABLED = False
DATABASE_RELEVANCY_CHECK_ENABLED = False

load_dotenv()


# Separate function to load configurations
def load_config(app, test_config=None):
    app.secret_key = os.environ.get(
        "FLASK_SECRET_KEY", "3d6f45a5fc12445dbac2f59c3b6c7cb1"
    )
    app.config["CAS_SERVER"] = "https://secure.its.yale.edu/cas"

    if test_config:
        # Load test configuration
        app.config.update(test_config)
        if "COURSE_QUERY_LIMIT" in app.config:
            global COURSE_QUERY_LIMIT
            COURSE_QUERY_LIMIT = app.config["COURSE_QUERY_LIMIT"]
        if "SAFETY_CHECK_ENABLED" in app.config:
            global SAFETY_CHECK_ENABLED
            SAFETY_CHECK_ENABLED = app.config["SAFETY_CHECK_ENABLED"]
        if "DATABASE_RELEVANCY_CHECK_ENABLED" in app.config:
            global DATABASE_RELEVANCY_CHECK_ENABLED
            DATABASE_RELEVANCY_CHECK_ENABLED = app.config[
                "DATABASE_RELEVANCY_CHECK_ENABLED"
            ]
        if "FLASK_SECRET_KEY" in app.config:
            app.secret_key = app.config["FLASK_SECRET_KEY"]
    else:
        # Load configuration from environment variables
        app.config["MONGO_URI"] = os.getenv("MONGO_URI")


# Separate function to initialize database
def init_database(app):
    if "MONGO_URI" in app.config:
        client = MongoClient(app.config["MONGO_URI"])
        db = client["course_db"]
        app.config["courses"] = db["parsed_courses"]
        app.config["profiles"] = db["user_profile"]

        # else, set to None or Mock in case of testing


def create_app(test_config=None):
    app = Flask(__name__)
    CORS(app)
    cas = CAS(app)
    app.config["CAS_SERVER"] = "https://secure.its.yale.edu/cas"

    load_config(app, test_config)
    init_database(app)

    # Define your routes here
    @app.route("/login", methods=["GET"])
    def login():
        return redirect(url_for("cas.login"))

    @app.route("/logout", methods=["GET"])
    def logout():
        session.clear()
        return redirect(url_for("cas.logout"))

    @app.route("/route_after_login", methods=["GET"])
    @login_required
    def route_after_login():
        # Handle what happens after successful login
        return "Logged in as " + session["CAS_USERNAME"]

    @app.route("/validate_ticket", methods=["POST"])
    def validate_cas_ticket():
        data = request.get_json()
        ticket = data.get("ticket")
        service_url = data.get("service_url")
        print(f"Received ticket: {ticket}, service URL: {service_url}")  # Log details

        if not ticket or not service_url:
            return jsonify({"error": "Ticket or service URL not provided"}), 400

        cas_validate_url = "https://secure.its.yale.edu/cas/serviceValidate"
        params = {"ticket": ticket, "service": service_url}
        response = requests.get(cas_validate_url, params=params)

        if response.status_code == 200:
            # Parse the XML response
            root = ET.fromstring(response.content)

            # Namespace in the XML response
            ns = {"cas": "http://www.yale.edu/tp/cas"}

            # Check for authentication success
            if root.find(".//cas:authenticationSuccess", ns) is not None:
                user = root.find(".//cas:user", ns).text
                # Optionally handle proxyGrantingTicket if you need it
                return jsonify({"isAuthenticated": True, "user": user})
            else:
                return jsonify({"isAuthenticated": False}), 401
        else:
            print("response status is not 200")
            return jsonify({"isAuthenticated": False}), 401

    @app.route("/api/save_chat", methods=["POST"])
    def save_chat():
        try:
            chat_data = request.get_json()
            collection = app.config["courses"]
            result = collection.insert_one(chat_data)
            return jsonify({"status": "success", "id": str(result.inserted_id)}), 201
        except Exception as e:
            return jsonify({"status": "error", "message": str(e)}), 500

    @app.route("/api/reload_chat", methods=["POST"])
    def reload_chat():
        try:
            data = request.get_json()
            chat_id = data.get("chat_id")
            collection = app.config["courses"]
            chat = collection.find_one({"_id": str(chat_id)})
            if chat:
                return jsonify({"status": "success", "chat": chat}), 200
            else:
                return jsonify({"status": "not found"}), 404
        except Exception as e:
            return jsonify({"status": "error", "message": str(e)}), 500

    @app.route("/api/verify_course_code", methods=["POST"])
    def verify_course_code():
        try:
            data = request.get_json()

            # uid = data.get("uid")
            # if not uid:
            #     return jsonify({"error": "No uid provided"}), 400

            course_code = data["search"]
            course_collection = app.config["courses"]
            user_collection = app.config["profiles"]
            course = course_collection.find_one({"course_code": course_code})
            if course:
                # insert into database
                # result = user_collection.update_one(
                #     {"uid": uid}, {"$addToSet": {"courses": course_code}}
                # )
                return jsonify(
                    {"status": "success", "course": course["course_code"]}
                ), 200
            else:
                return jsonify({"status": "invalid course code"}), 404
        except Exception as e:
            return jsonify({"status": "error", "message": str(e)}), 500

    @app.route("/api/delete_course_code", methods=["POST"])
    def delete_course_code():
        try:
            data = request.get_json()

            uid = data.get("uid")
            if not uid:
                return jsonify({"error": "No uid provided"}), 400

            course_code = data["search"]
            course_collection = app.config["courses"]
            user_collection = app.config["profiles"]
            course = course_collection.find_one({"course_code": course_code})
            if course:
                # insert into database
                result = user_collection.update_one(
                    {"uid": uid}, {"$pull": {"courses": course_code}}
                )
                return jsonify(
                    {"status": "success", "course": course["course_code"]}
                ), 200
            else:
                return jsonify({"status": "invalid course code"}), 404
        except Exception as e:
            return jsonify({"status": "error", "message": str(e)}), 500

    # must only call after checking if the user exists
    @app.route("/api/user/create", methods=["POST"])
    def create_user_profile():
        data = request.get_json()
        uid = data.get("uid", None)
        if not uid:
            return jsonify({"error": "No uid provided"})

        collection = app.config["profiles"]

        user_profile = {
            "uid": uid,
            "chat_history": [],
            "courses": [],
            "name": "",
        }

        result = collection.insert_one(user_profile)
        user_profile["_id"] = str(result.inserted_id)

        return jsonify(user_profile)

    @app.route("/api/user/profile", methods=["POST"])
    def get_user_profile():
        data = request.get_json()
        uid = data.get("uid", None)
        if not uid:
            return jsonify({"error": "No uid provided"})

        collection = app.config["profiles"]
        user_profile = collection.find_one({"uid": uid})
        if not user_profile:
            return jsonify({"error": "No user profile found"}), 404

        # Convert ObjectId to string
        user_profile["_id"] = str(user_profile["_id"])

        return jsonify(user_profile)

    def update_user_profile(uid, update):
        collection = app.config["profiles"]
        user_profile = collection.find_one({"uid": uid})
        collection.update_one({"uid": uid}, {"$set": update})
        user_profile = collection.find_one({"uid": uid})
        user_profile["_id"] = str(user_profile["_id"])
        return jsonify(user_profile)

    @app.route("/api/user/update/name", methods=["POST"])
    def update_user_name():
        data = request.get_json()
        uid = data.get("uid", None)
        name = data.get("name", None)
        if not uid:
            return jsonify({"error": "No uid provided"})
        if not name:
            return jsonify({"error": "No name provided"})
        return update_user_profile(uid, {"name": name})

    @app.route("/api/chat/create_chat", methods=["POST"])
    def create_new_chat():
        data = request.get_json()
        uid = data.get("uid", None)
        init_message = data.get("message", None)
        if not uid:
            return jsonify({"error": "No uid provided"})

        chat_id = str(uuid4())
        if init_message is not None:
            new_chat = {"chat_id": chat_id, "messages": [init_message]}
        else:
            new_chat = {"chat_id": chat_id, "messages": []}

        collection = app.config["profiles"]
        result = collection.update_one(
            {"uid": uid}, {"$push": {"chat_history": new_chat}}
        )
        return jsonify({"status": "success"}), 200

    @app.route("/api/chat/append_message", methods=["POST"])
    def append_message_to_chat():
        data = request.get_json()
        uid = data.get("uid", None)
        chat_id = data.get("chat_id", None)
        message = data.get("message", None)
        if not uid:
            return jsonify({"error": "No uid provided"})
        if not message:
            return jsonify({"error": "No message provided"})
        if not chat_id:
            return jsonify({"error": "No chat_id provided"})

        collection = app.config["profiles"]
        # find the user with the chat id
        user_profile = collection.find_one({"uid": uid})
        if not user_profile:
            return jsonify({"error": "No user profile found"}), 404
        # update the selected chat by appending the message
        for chat in user_profile["chat_history"]:
            if chat["chat_id"] == chat_id:
                chat["messages"].append(message)
                break

        result = collection.update_one(
            {"uid": uid}, {"$set": {"chat_history": user_profile["chat_history"]}}
        )
        return jsonify({"status": "success"}), 200

    @app.route("/api/chat/delete_chat", methods=["POST"])
    def delete_chat():
        data = request.get_json()
        uid = data.get("uid", None)
        chat_id = data.get("chat_id", None)
        if not uid:
            return jsonify({"error": "No uid provided"})
        if not chat_id:
            return jsonify({"error": "No chat_id provided"})

        collection = app.config["profiles"]
        # use $pull to remove the chat with the chat_id
        result = collection.update_one(
            {"uid": uid}, {"$pull": {"chat_history": {"chat_id": chat_id}}}
        )
        return jsonify({"status": "success"}), 200

    @app.route("/api/slug", methods=["POST"])
    def get_chat_history_slug():
        data = request.get_json()
        user_messages = data.get("message", None)
        user_messages_ = user_messages.copy()
        user_messages_.append(
            {
                "role": "user",
                "content": "Write a descriptive title (3-4 words) for the topic of our conversation with no puncutation. Do not include 'discussion' or 'chat' in the title.",
            }
        )

        response = chat_completion_request(messages=user_messages_)
        try:
            response = response.choices[0].message.content
            return jsonify({"slug": response})
        except:
            return jsonify({"slug": "Untitled"})

    @app.route("/api/chat", methods=["POST"])
    def chat():
        data = request.get_json()
        user_messages = data.get("message", None)

        filter_season_codes = data.get(
            "season_codes", None
        )  # assume it is an array of season code
        filter_subjects = data.get("subject", None)
        filter_areas_and_skills = data.get("areas", None)
        if filter_areas_and_skills:
            filter_skills = [
                area for area in filter_areas_and_skills if area in ["Hu", "So", "Sc"]
            ]
            filter_areas = [
                area for area in filter_areas_and_skills if area in ["QR", "WR"]
            ]
        else:
            filter_skills = None
            filter_areas = None

        if not user_messages:
            return jsonify({"error": "No message provided"})

        # remove id before sending to OpenAI
        for message in user_messages:
            if "id" in message:
                del message["id"]
            if message["role"] == "ai":
                message["role"] = "assistant"

        # print(user_messages)

        if SAFETY_CHECK_ENABLED:
            # for safety check, not to be included in final response
            user_messages_safety_check = user_messages.copy()
            user_messages_safety_check.append(
                {
                    "role": "user",
                    "content": 'Am I asking for help with courses or academics? Answer "yes" or "no".',
                }
            )

            response_safety_check = chat_completion_request(
                messages=user_messages_safety_check
            )
            response_safety_check = response_safety_check.choices[0].message.content

            if "no" in response_safety_check.lower():
                response = "I am sorry, but I can only assist with questions related to courses or academics at this time."
                json_response = {"response": response, "courses": []}
                print("failed safety check")
                return jsonify(json_response)
            else:
                print("passed safety check")

        # adding system message if user message does not include a system message header
        if user_messages[0]["role"] != "system":
            user_messages.insert(
                0,
                {
                    "role": "system",
                    "content": "Your name is Eli. You are a helpful assistant for Yale University students to ask questions about courses and academics.",
                },
            )

        if DATABASE_RELEVANCY_CHECK_ENABLED:
            # checking if database query is necessary
            user_messages_database_relevancy_check = user_messages.copy()
            user_messages_database_relevancy_check.append(
                {
                    "role": "user",
                    "content": 'Will you be able to better answer my question with access to specific courses at Yale University? If you answer "yes", you will be provided with courses that are semantically similar to my question. Answer "yes" or "no".',
                }
            )

            user_messages_database_relevancy_check = chat_completion_request(
                messages=user_messages_database_relevancy_check
            )
            response_user_messages_database_relevancy_check = (
                user_messages_database_relevancy_check.choices[0].message.content
            )

            if "no" in response_user_messages_database_relevancy_check.lower():
                response = chat_completion_request(messages=user_messages)
                response = response.choices[0].message.content
                json_response = {"response": response, "courses": []}
                print("no need to query database for course information")
                return jsonify(json_response)
            else:
                print("need to query database for course information")

        # create embedding for user message to query against vector index
        vector_search_prompt_generation = user_messages.copy()
        vector_search_prompt_generation.append(
            {
                "role": "system",
                "content": "What would be a good search query (in conventional english) to query against the Yale courses database that addresses the user needs?",
            }
        )

        print(vector_search_prompt_generation)
        response = chat_completion_request(messages=vector_search_prompt_generation)
        response = response.choices[0].message.content
        print("")
        print("Completion Request: Vector Search Prompt")
        print(response)
        print("")

        query_vector = create_embedding(response)

        collection = app.config["courses"]

        aggregate_pipeline = {
            "$vectorSearch": {
                "index": "parsed_courses_title_description_index",
                "path": "embedding",
                "queryVector": query_vector,
                "numCandidates": 30,
                "limit": COURSE_QUERY_LIMIT,
            }
        }

        filtered_response = chat_completion_request(messages=user_messages, tools=tools)
        print(filtered_response)

        filtered_data = json.loads(
            filtered_response.choices[0].message.tool_calls[0].function.arguments
        )
        print("")
        print("Completion Request: Filtered Response")
        print(filtered_data)
        print("")

        natural_filter_subject = filtered_data.get("subject", None)
        natural_filter_season_codes = filtered_data.get("season_code", None)
        natural_filter_areas = filtered_data.get("areas", None)
        natural_filter_skills = filtered_data.get("skills", None)

        filters = []

        # Apply filters for season codes
        if filter_season_codes:
            filters.append({"season_code": {"$in": filter_season_codes}})
        elif natural_filter_season_codes:
            filters.append({"season_code": {"$in": [natural_filter_season_codes]}})

        # Apply filters for subjects
        if filter_subjects:
            filters.append({"subject": {"$in": filter_subjects}})
        elif natural_filter_subject:
            filters.append({"subject": {"$in": [natural_filter_subject]}})

        # Apply filters for areas
        if filter_areas:
            filters.append({"areas": {"$in": filter_areas}})
        elif natural_filter_areas:
            filters.append({"areas": {"$in": [natural_filter_areas]}})

        # Apply filters for skills
        if filter_skills:
            filters.append({"skills": {"$in": filter_skills}})
        elif natural_filter_skills:
            filters.append({"skills": {"$in": [natural_filter_skills]}})

        # If there are any filters, add them to the vectorSearch pipeline
        if filters:
            aggregate_pipeline["$vectorSearch"]["filter"] = {"$and": filters}

        print(aggregate_pipeline["$vectorSearch"]["filter"])

        # print(aggregate_pipeline)
        database_response = collection.aggregate([aggregate_pipeline])
        database_response = list(database_response)

        recommended_courses = [
            {
                "season_code": course["season_code"],
                "course_code": course["course_code"],
                "title": course["title"],
                "description": course["description"],
                "areas": course["areas"],
                "sentiment_label": course["sentiment_info"]["final_label"],
                "sentiment_score": course["sentiment_info"]["final_proportion"],
            }
            for course in database_response
        ]

        if recommended_courses:
            recommendation_prompt = (
                "Here are some courses that might be relevant to the user request:\n\n"
            )
            for course in recommended_courses:
                recommendation_prompt += f'{course["course_code"]}: {course["title"]}\n{course["description"]}\n\n'
            recommendation_prompt += "Incorporate specific course information in your response to me if it is relevant to the user request. If you include any course titles, make sure to wrap it in **double asterisks**. Do not order them in a list. Do not refer to any courses not in this list"

        else:
            recommendation_prompt = "Apologize to the user for not being able to fullfill their request, your response should begin with 'I'm sorry. I tried to search for courses that match your criteria but couldn't find any' verbatim"
        user_messages.append({"role": "system", "content": recommendation_prompt})

        print(user_messages)

        response = chat_completion_request(messages=user_messages)

        response = response.choices[0].message.content

        print()
        print(user_messages)
        print(response)

        json_response = {"response": response, "courses": recommended_courses}

        # print("")
        # print("Completion Request: Recommendation")
        # print(json_response)
        # print("")

        return jsonify(json_response)

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(debug=True, port=8000)
