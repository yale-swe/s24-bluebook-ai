from tenacity import retry, wait_random_exponential, stop_after_attempt
import os
from openai import OpenAI
import json
from dotenv import load_dotenv

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Open the JSON file
with open('course_subjects.json', 'r') as file:
    # Load the JSON data into a Python list
    subjects = json.load(file)

tools = [
    {
        "type": "function",
        "function": {
        "name": "CourseFilter",
        "description": "Provide filters for a course based on conditions.", 
        "parameters": {
            "type": "object",
            "properties": {
                "subject_code": {
                    "type": "string",
                    "enum": [str(key) for key in subjects.keys()],
                    "description": "A code for the subject of instruction",
                },
                "rating": {
                    "type": "number",
                    "description": "The rating (a number with one significant digit) for the class (0 - 4). If a number is not provided, interpret the given opinion to fit the range. A good, or average, class should be 3.5",
                },
                "comparison_operator_rating": {
                    "type": "string",
                    "enum": ["$lt", "$gt", "$gte", "$lte"],
                    "description": "A comparison operator for the class rating",
                },
                "workload": {
                    "type": "number",
                    "description": "The workload (a number with one significant digit) for the class (0 - 4). If a number is not provided, interpret the given opinion to fit the range.",
                },
                "comparison_operator_workload": {
                    "type": "string",
                    "enum": ["$lt", "$gt", "$gte", "$lte"],
                    "description": "A comparison operator for the class workload",
                },             
            },
            "required": ["comparison_operator_rating", "rating"],
        },
        }
    }
]

client = OpenAI(api_key=OPENAI_API_KEY)

@retry(wait=wait_random_exponential(multiplier=1, max=40), stop=stop_after_attempt(3))
def create_embedding(text, model='text-embedding-3-small'):
    try:
        response = client.embeddings.create(
            input=text,
            model="text-embedding-3-small"
        )
        return response.data[0].embedding
    except Exception as e:
        print("Unable to generate embedding")
        print(f"Exception: {e}")
        return e

@retry(wait=wait_random_exponential(multiplier=1, max=40), stop=stop_after_attempt(3))
def chat_completion_request(messages, tools=None, tool_choice=None, model='gpt-4'):
    try:
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            tools=tools,
            tool_choice=tool_choice,
        )
        return response
    except Exception as e:
        print("Unable to generate ChatCompletion response")
        print(f"Exception: {e}")
        return e
    
