"""
A module for interacting with the OpenAI API, including creating 
embeddings and generating chat completions.
"""

import os
import json
from tenacity import retry, wait_random_exponential, stop_after_attempt
import openai
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

with open("course_subjects.json", "r", encoding="utf-8") as file:
    subjects = json.load(file)

api_tools = [
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
                        "description": """The rating (a number with one significant 
                        digit) for the class (0 - 4). If a number is not provided, 
                        interpret the given opinion to fit the range. A good, or 
                        average, class should be 3.5""",
                    },
                    "comparison_operator_rating": {
                        "type": "string",
                        "enum": ["$lt", "$gt", "$gte", "$lte"],
                        "description": "A comparison operator for the class rating",
                    },
                    "workload": {
                        "type": "number",
                        "description": """The workload (a number with one significant 
                        digit) for the class (0 - 4). If a number is not provided, 
                        interpret the given opinion to fit the range.""",
                    },
                    "comparison_operator_workload": {
                        "type": "string",
                        "enum": ["$lt", "$gt", "$gte", "$lte"],
                        "description": "A comparison operator for the class workload",
                    },
                },
                "required": ["comparison_operator_rating", "rating"],
            },
        },
    }
]

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

@retry(wait=wait_random_exponential(multiplier=1, max=40), stop=stop_after_attempt(3))
def create_embedding(text, model="text-embedding-3-small"):
    """
    Generates an embedding for the given text using the specified model.

    Parameters:
    - text (str): The text to generate an embedding for.
    - model (str): The model to use for generating the embedding.

    Returns:
    - The embedding as a list of floats or an exception if the request fails.
    """
    try:
        response = client.embeddings.create(
            input=text, model=model
        )
        return response.data[0].embedding
    except openai.InternalServerError as e:
        print("Unable to generate embedding")
        print(f"Exception: {e}")
        return e

@retry(wait=wait_random_exponential(multiplier=1, max=40), stop=stop_after_attempt(3))
def chat_completion_request(
    messages, tools_param=None, tool_choice=None, model="gpt-3.5-turbo"
):
    """
    Requests a chat completion from the OpenAI API using the provided messages and tools.

    Parameters:
    - messages (list): A list of message dictionaries for the chat.
    - tools_param (list, optional): Tools to use for the chat completion.
    - tool_choice (str, optional): The choice of tool to use for the chat completion.
    - model (str): The model to use for the chat completion.

    Returns:
    - The API response for the chat completion.
    """
    try:
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            tools=tools_param,
            tool_choice=tool_choice,
        )
        return response
    except Exception as e:
        raise e
