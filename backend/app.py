from flask import Flask, request, jsonify
import os
from dotenv import load_dotenv
from lib import chat_completion_request, create_embedding
import json

from pymongo.mongo_client import MongoClient

uri = "mongodb+srv://bluebookairoot:<password>@bluebookcluster.0hf4pzi.mongodb.net/?retryWrites=true&w=majority&appName=BluebookCluster"

# connect to the MongoDB cluster
client = MongoClient(uri)
db = client['bluebookai']
collection = db['course-info']

try:
    client.admin.command('ping')
    print("Pinged your deployment. You successfully connected to MongoDB!")
except Exception as e:
    print(e)

app = Flask(__name__)

load_dotenv()

@app.route('/chat', methods=['POST'])
def chat():
    data = request.get_json()
    if 'message' not in data:
        return jsonify({"error": "Missing 'messages' in request body"}), 400
    
    user_messages = data['message']
    response = chat_completion_request(messages=user_messages)
    message = response.choices[0].message
    print(message)
    # if message.tool_calls is None:
    #     return 'success'
    #     args = json.loads(message.tool_calls[0].function.arguments)
    #     query_vector = create_embedding(user_messages[-1]['content'])
    #     database_response = collection.aggregate([
    #         {
    #         '$vectorSearch': {
    #             'index': 'course-rating-index',
    #             'path': 'embedding',
    #             'filter': {
    #                 'rating': {
    #                     args['operator']: args['rating']
    #                 }
    #             },
    #             'queryVector': query_vector,
    #             'numCandidates': 5,
    #             'limit': 5
    #         }
    #         }
    #     ])
    #     # print(database_response)

    #     top_class = list(database_response)[0]
    #     json_response = {
    #         'title': top_class['title'],
    #         'rating': top_class['rating'],
    #     }
    #     return jsonify(json_response)

    # "{\"operator\":\"$gt\",\"rating\":4}"
    
    # ChatCompletionMessage(content=None, role='assistant', function_call=None, tool_calls=[ChatCompletionMessageToolCall(id='call_Ub07GeA6kaC2OZ8b8KlVmtZz', function=Function(arguments='{\n  "subject_code": "CPSC",\n  "rating": 3.5,\n  "comparison_operator_rating": "$gte",\n  "workload": 1,\n  "comparison_operator_workload": "$lte"\n}', name='CourseFilter'), type='function')])

    query_vector = create_embedding(user_messages[-1]['content'])

    print(user_messages[-1])
    database_response = collection.aggregate([
            {
            '$vectorSearch': {
                'index': 'course-rating-index',
                'path': 'embedding',
                'queryVector': query_vector,
                'numCandidates': 5,
                'limit': 5
            }
            }
        ])

    classes = list(database_response)
    # top_class = classes[0]
    print([c['title'] for c in classes])
    top_class = classes[0]
    json_response = {
        # 'message': [{
        #     'role': response.choices[0].message.role,
        #     'content': response.choices[0].message.content,
        # }]
        'title': top_class['title'],
        # 'rating': top_class['rating'],
    }

    return jsonify(json_response)

if __name__ == '__main__':
    app.run(debug=True)
