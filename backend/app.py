from flask import Flask, request, jsonify
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

try:
    client.admin.command('ping')
    print("Pinged your deployment. You successfully connected to MongoDB!")
except Exception as e:
    print(e)

# flask
app = Flask(__name__)

@app.route('/api/chat', methods=['POST'])
def chat():

    data = request.get_json()    
    user_messages = data['message']
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
            'description': course['description']
        } for course in database_response
    ]
    
    recommendation_prompt = f'Here are some courses that might be relevant to the user request:\n\n'
    for course in recommended_courses:
        recommendation_prompt += f'{course["course_code"]}: {course["title"]}\n{course["description"]}\n\n'
    recommendation_prompt += 'Provide a response to the user. Incorporate this information only if it is relevant to the user request.'

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
