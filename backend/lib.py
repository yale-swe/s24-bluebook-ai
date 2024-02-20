from tenacity import retry, wait_random_exponential, stop_after_attempt
import os
from openai import OpenAI

tools = [
    {
        "type": "function",
        "function": {
            "name": "filter_classes_by_rating",
            "description": "",
            "parameters": {
                "type": "object",
                "properties": {
                    "operator": {
                        "type": "string",
                        "enum": ["$gt", "$lt", '$gte', '$lte', '$eq'],
                        "description": "The operator to use for the filter",
                    },
                    "rating": {
                        "type": "number",
                        "description": "The rating to filter by",
                    },
                },
                "required": ["operator", "rating"],
            },
        }
    },
]

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

@retry(wait=wait_random_exponential(multiplier=1, max=40), stop=stop_after_attempt(3))
def chat_completion_request(messages, tools=tools, tool_choice=None, model='gpt-3.5-turbo'):
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
