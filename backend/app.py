from flask import Flask, request, jsonify
from flask_cors import CORS
import os
from dotenv import load_dotenv
from lib import chat_completion_request, create_embedding
import json
from pymongo.mongo_client import MongoClient

COURSE_QUERY_LIMIT = 5

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
CORS(app)

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
    
    # checking if database query is necessary
    user_messages_database_relevancy_check = user_messages.copy()
    user_messages_database_relevancy_check.append({
        'role': 'user',
        'content': 'Will you be able to better answer my questions with information about specific courses related to the user query at Yale University? You should answer "yes" if you need information about courses at Yale that you don\'t have, otherwise you should answer "no".'
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
    recommendation_prompt += 'Provide a response to the user. Incorporate specific course information if it is relevant to the user request.'

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