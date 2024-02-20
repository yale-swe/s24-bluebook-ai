from flask import Flask, request, jsonify
import os
from dotenv import load_dotenv
from lib import chat_completion_request

from pymongo.mongo_client import MongoClient

uri = "mongodb+srv://dbUser:<password>@cluster0.blvdnja.mongodb.net/?retryWrites=true&w=majority"

# connect to the MongoDB cluster
client = MongoClient(uri)
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
    if message.tool_calls is not None:
        json_response = message.tool_calls[0].function.arguments
        
    
    # ChatCompletionMessage(content=None, role='assistant', function_call=None, tool_calls=[ChatCompletionMessageToolCall(id='call_Ub07GeA6kaC2OZ8b8KlVmtZz', function=Function(arguments='{\n  "subject_code": "CPSC",\n  "rating": 3.5,\n  "comparison_operator_rating": "$gte",\n  "workload": 1,\n  "comparison_operator_workload": "$lte"\n}', name='CourseFilter'), type='function')])

    json_response = {
        'message': [{
            'role': response.choices[0].message.role,
            'content': response.choices[0].message.content,
        }]
    }

    return jsonify(json_response)

if __name__ == '__main__':
    app.run(debug=True)
