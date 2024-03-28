# Flask Backend

This is the backend for the project, built using Flask.

## Installation

1. Install the required dependencies:

    ```bash
    conda env create -f environment.yml
    conda activate bluebook
    ```

2. You will need to have your IP address allowlisted from Mongo to query the database.
3. You will also need to create an `.env` file that contains your API keys:

```
MONGO_URI="mongodb+srv://xxx"
OPENAI_API_KEY="sk-xxx"
```

## Usage

1. Start the Flask server:

    ```bash
    python app.py
    ```

2. The server will start running on `http://localhost:8000`.

3. Use your favorite API client (e.g., Postman) to send a POST request to `http://localhost:8000/api/chat` with the following JSON payload:

    ```json
    {
        "role": "user",
        "content": "Tell me some courses about personal finance"
    }
    ```

    You should receive a response with the recommended courses like this:

    ```json
    {
        "courses": [
            {
                "course_code": "ECON 436",
                "description": "How much should I be saving at age 35? How much of my portfolio should be invested in stocks at age 50? Which mortgage should I choose, and when should I refinance it? How much can I afford to spend per year in retirement? This course covers prescriptive models of personal saving, asset allocation, borrowing, and spending. The course is designed to answer questions facing anybody who manages their own money or is a manager in an organization that is trying to help clients manage their money.",
                "title": "Personal Finance"
            },
            ...
        ],
        "response": "To learn more about personal finance, you can start by taking courses or workshops that focus on financial management, budgeting, investing, and retirement planning. Some universities and educational platforms offer online courses on personal finance, such as ECON 436: Personal Finance and ECON 361: Corporate Finance. Additionally, you can explore resources like books, podcasts, and websites dedicated to personal finance advice and tips. It may also be helpful to consult with a financial advisor or planner for personalized guidance on managing your finances effectively."
    }
    ```
