from urllib.parse import urljoin
from flask import Flask, request, jsonify, session, redirect, url_for
from flask_cors import CORS
from flask_cas import CAS, login_required
import os
from dotenv import load_dotenv
from lib import chat_completion_request, create_embedding
import json
from pymongo.mongo_client import MongoClient
import requests
import xml.etree.ElementTree as ET

COURSE_QUERY_LIMIT = 5
SAFETY_CHECK_ENABLED = False
DATABASE_RELEVANCY_CHECK_ENABLED = True

load_dotenv()

# database initialization
uri = os.getenv('MONGO_URI')
client = MongoClient(uri)
db = client['course_db']
collection = db['parsed_courses']

# mongo connection
try:
    client.admin.command('ping')
    print("Pinged your deployment. You successfully connected to MongoDB!")
except Exception as e:
    print(e)

# flask
app = Flask(__name__)
app.secret_key = os.environ.get('FLASK_SECRET_KEY', '3d6f45a5fc12445dbac2f59c3b6c7cb1')
CORS(app)
CAS(app)

app.config['CAS_SERVER'] = 'https://secure.its.yale.edu/cas'

@app.route('/login', methods=['GET'])
def login():
    return redirect(url_for('cas.login'))

@app.route('/logout', methods=['GET'])
def logout():
    session.clear()
    return redirect(url_for('cas.logout'))

@app.route('/route_after_login', methods=['GET'])
@login_required
def route_after_login():
    # Handle what happens after successful login
    return 'Logged in as ' + session['CAS_USERNAME']

@app.route('/validate_ticket', methods=['POST'])
def validate_cas_ticket():
    data = request.get_json()
    ticket = data.get("ticket")
    service_url = data.get("service_url")
    print(f"Received ticket: {ticket}, service URL: {service_url}")  # Log details

    if not ticket or not service_url:
        return jsonify({"error": "Ticket or service URL not provided"}), 400

    cas_validate_url = 'https://secure.its.yale.edu/cas/serviceValidate'
    params = {'ticket': ticket, 'service': service_url}
    response = requests.get(cas_validate_url, params=params)

    if response.status_code == 200:
        # Parse the XML response
        root = ET.fromstring(response.content)

        # Namespace in the XML response
        ns = {'cas': 'http://www.yale.edu/tp/cas'}
        
        # Check for authentication success
        if root.find('.//cas:authenticationSuccess', ns) is not None:
            user = root.find('.//cas:user', ns).text
            # Optionally handle proxyGrantingTicket if you need it
            return jsonify({"isAuthenticated": True, "user": user})
        else:
            return jsonify({"isAuthenticated": False}), 401
    else:
        print("response status is not 200")
        return jsonify({"isAuthenticated": False}), 401
    
@app.route('/api/chat', methods=['POST'])
def chat():

    data = request.get_json()
    user_messages = data['message']

    # remove id before sending to OpenAI
    for message in user_messages:
        if 'id' in message:
            del message['id']
        if message['role'] == 'ai':
            message['role'] = 'assistant'

    print(user_messages)

    if SAFETY_CHECK_ENABLED:
        # for safety check, not to be included in final response
        user_messages_safety_check = user_messages.copy()
        user_messages_safety_check.append({
            'role': 'user',
            'content': 'Am I asking for help with courses or academics? Answer "yes" or "no".'
        })

        response_safety_check = chat_completion_request(messages=user_messages_safety_check)
        response_safety_check = response_safety_check.choices[0].message.content
        
        if 'no' in response_safety_check.lower():
            response = 'I am sorry, but I can only assist with questions related to courses or academics at this time.'
            json_response = {
                'response': response,
                'courses': []
            }
            print('failed safety check')
            return jsonify(json_response)
        else:
            print('passed safety check')
    
    # adding system message if user message does not include a system message header
    if user_messages[0]['role'] != 'system':
        user_messages.insert(0, {
            'role': 'system',
            'content': 'Your name is Eli. You are a helpful assistant for Yale University students to ask questions about courses and academics.'
        })
    
    if DATABASE_RELEVANCY_CHECK_ENABLED:
        # checking if database query is necessary
        user_messages_database_relevancy_check = user_messages.copy()
        user_messages_database_relevancy_check.append({
            'role': 'user',
            'content': 'Will you be able to better answer my question with access to specific courses at Yale University? If you answer "yes", you will be provided with courses that are semantically similar to my question. Answer "yes" or "no".'
        })

        user_messages_database_relevancy_check = chat_completion_request(messages=user_messages_database_relevancy_check)
        response_user_messages_database_relevancy_check = user_messages_database_relevancy_check.choices[0].message.content

        if 'no' in response_user_messages_database_relevancy_check.lower():
            response = chat_completion_request(messages=user_messages)
            response = response.choices[0].message.content
            json_response = {
                'response': response,
                'courses': []
            }
            print('no need to query database for course information')
            return jsonify(json_response)
        else:
            print('need to query database for course information')

    # create embedding for user message to query against vector index
    query_vector = create_embedding(user_messages[-1]['content'])

    database_response = collection.aggregate([
        {
            '$vectorSearch': {
                'index': 'parsed_courses_title_description_index',
                'path': 'embedding',
                # 'filter': {
                #     'rating': {
                #         args['operator']: args['rating']
                #     }
                # },
                'queryVector': query_vector,
                'numCandidates': 30,
                'limit': COURSE_QUERY_LIMIT
            }
        }
    ])

    database_response = list(database_response)        

    recommended_courses = [
        {
            'course_code': course['course_code'],
            'title': course['title'],
            'description': course['description'],
            'areas': course['areas']
        } for course in database_response
    ]

    recommendation_prompt = f'Here are some courses that might be relevant to the user request:\n\n'
    for course in recommended_courses:
        recommendation_prompt += f'{course["course_code"]}: {course["title"]}\n{course["description"]}\n\n'
    recommendation_prompt += 'Provide a response to the user. Incorporate specific course information if it is relevant to the user request. If you include any course titles, make sure to wrap it in **double asterisks**. Do not order them in a list.'

    user_messages.append({
        'role': 'system',
        'content': recommendation_prompt
    })

    response = chat_completion_request(messages=user_messages)
    response = response.choices[0].message.content


    json_response = {
        'response': response,
        'courses': recommended_courses
    }

    return jsonify(json_response)

if __name__ == '__main__':
    app.run(debug=True, port=8000)
