# BluebookAI

Course selections play a pivotal role in shaping student learning experiences at Yale. Each semester, Yale has a vast array of course offerings, and it is difficult for students to select specific courses that fit their needs and interests. Beyond the official Yale Course Search, students often turn to CourseTable for additional insights from other students’ reviews and experiences.

With CourseTable, students retrieve information using keyword search, filtering, and sorting across classes offered in current and previous semesters. However, CourseTable currently uses exact match only, which can be less helpful when the student doesn’t know what specific course(s) they are searching for. For example, a student who searches for “DevOps” may not see CPSC 439/539 Software Engineering in returned search results.

In this project, we aim to enhance students’ course selection experience by augmenting CourseTable with a natural language interface that can provide customized course recommendations in response to student queries. By supplying more relevant and dynamic results and expanding students’ means of interaction with course data, this will enable students to more easily and effectively determine the best course schedule for themselves.

## Get Started

### Frontend

0. If you don't already have Node.js installed, you can download it [here](https://nodejs.org/en/download/).
1. Enter the `frontend` directory and install the dependencies:

   ```bash
   cd frontend
   npm install
   ```

2. Start the Next.js app:

   ```bash
   npm run dev
   ```

### Backend

1. Enter the `backend` directory, create a virtual environment, activate it, and install the dependencies. Make sure you have Python 3.10+ installed.

    ```bash
    cd backend
    python -m venv bluebook_env
    source bluebook_env/bin/activate (windows: .\bluebook_env\Scripts\activate)
    pip install -r ../requirements.txt
    ```

2. You will also need to create `.env` in the the `backend` directory that contains your API key to OpenAI and the MongoDB URI. The `.env` file should look like this:

```
MONGO_URI="mongodb+srv://xxx"
OPENAI_API_KEY="sk-xxx"
```

Don't push your API key to this repo!

You can get an OpenAI API key [here](https://platform.openai.com/api-keys). The MongoDB URI is shared by the team. You will need to have your IP address allowlisted by MongoDB to query the database. Contact the team for access.

To run sentiment classification, first create a conda environment for Python 3 using the `backend/sentiment_classif_requirements.txt` file:

```bash
cd backend
conda create --name <env_name> --file sentiment_classif_requirements.txt
```

Activate the conda environment by running:

```bash
conda activate <env_name>
```

where `<env_name>` is your name of choice for the conda environment.

3. Start the Flask server:

   ```bash
   python app.py
   ```
4. Ask away!

![demo](./demo.png)

4.5. You can also use your favorite API client (e.g., Postman) to send a POST request to `http://localhost:8000/api/chat` with the following JSON payload:

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
## Deployment

The website is hosted using CloudFront distribution through AWS which is routed to a web server running on Elastic Beanstalk. The code for the frontend and backend are contained in two separate S3 buckets. To update the frontend, we run the following script

```cd frontend
export REACT_APP_API_URL=/api
npm run build
aws s3 sync out/ s3://bluebook-ai-frontend --acl public-read
```
To enable continuous syncing of the CloudFront distribution with the frontend-associated S3 bucket we write the following invalidation rule.

```
aws cloudfront create-invalidation --distribution-id bluebook-ai-frontend --paths "/*"
```

For running the Elastic Beanstalk web server, we use the aws EB CLI and run the follow commands in the backend/ folder
```
eb init
eb deploy
```
The CloudFront Distribution should have a routing link to the backend server through a behavior pointing to the EB instance.

## Running and Adding Tests

This repository contains tests for the backend. To run these tests, `pip install pytest` (if you haven't already), cd into backend and run
```
pytest
```
This runs the tests located in **`backend/test_app.py`**

The tests are also configured run automatically through GitHub Actions every time someone pushes to any branch or opens a pull request. You can find the workflow under  **`.github/workflows/python-app.yml`**

To generate a coverage report, first `pip install coverage`, then cd into backend and run
```
coverage run -m pytest
coverage html
```
then cd into htmlcov and run `open index.html`

### Adding Tests

Always check the import statements at the top of **`test_app.py`** and `pip install` anything that you didn't already.

The GitHub Actions workflow runs a single `pytest` command in the backend folder, so make sure your pytests are in the root directory and are named appropriately (filename begins with "test_...")

Some stuff to keep in mind while writing new tests

1. Locate the Correct Test File: Find the test file that corresponds to the module you are modifying or create a new one if your code is in a new module.
2. Test Function Naming: Begin your test function names with test_. This naming convention is necessary for pytest to recognize the function as a test.
3. Arrange, Act, Assert (AAA) Pattern: Structure your tests with the setup (Arrange), the action (Act), and the verification (Assert). This makes tests easy to read and understand.
4. Mock External Dependencies: Use mock or MagicMock to simulate external API calls, database interactions, and any other external processes.
5. Minimize Test Dependencies: Each test should be independent of others. Avoid shared state between tests.
6. Use Fixtures for Common Setup Code: If multiple tests share setup code, consider using pytest fixtures to centralize this setup logic.

Here's an example of a test complete with mocks and fixtures:

```python
@pytest.fixture
def client():
    mock_courses_collection = MagicMock()
    mock_courses_collection.aggregate.return_value = iter(
        [
            {
                "areas": ["Hu"],
                "course_code": "CPSC 150",
                "description": "Introduction to the basic ideas of computer science (computability, algorithm, virtual machine, symbol processing system), and of several ongoing relationships between computer science and other fields, particularly philosophy of mind.",
                "season_code": "202303",
                "sentiment_info": {
                    "final_label": "NEGATIVE",
                    "final_proportion": 0.9444444444444444,
                },
                "title": "Computer Science and the Modern Intellectual Agenda",
            },
        ]
    )

    mock_profiles_collection = MagicMock()
    mock_profiles_collection.aggregate.return_value = iter(
        [
            {
                "_id": {"$oid": "661c6bf1de004d9ab0e15604"},
                "uid": "bob",
                "chat_history": [
                    {"chat_id": "79f0c4a7-548b-4fce-9a90-aaa709936907", "messages": []},
                    {"chat_id": "c5b133b1-2f19-4c3c-8efc-0214c1540a75", "messages": []},
                ],
                "courses": [],
                "name": "hello",
                "email": "bluebookai@harvard.com",
            }
        ]
    )

    app = create_app(
        {
            "TESTING": True,
            "courses": mock_courses_collection,
            "profiles": mock_profiles_collection,
            "MONGO_URL": "TEST_URL",
            "COURSE_QUERY_LIMIT": 5,
            "SAFETY_CHECK_ENABLED": True,
            "DATABASE_RELEVANCY_CHECK_ENABLED": True,
        }
    )
    with app.test_client() as client:
        yield client
```
```python
@pytest.fixture
def mock_chat_completion_complete():
    with patch("app.chat_completion_request") as mock:
        # Common setup for tool call within the chat message
        function_mock = MagicMock()
        function_mock.arguments = '{"season_code": "202303"}'

        tool_call_mock = MagicMock()
        tool_call_mock.function = function_mock

        message_mock_with_tool_calls = MagicMock()
        message_mock_with_tool_calls.content = "yes"
        message_mock_with_tool_calls.tool_calls = [tool_call_mock]

        message_mock_mock_response = MagicMock()
        message_mock_mock_response.content = "Mock response based on user message"
        message_mock_mock_response.tool_calls = [tool_call_mock]

        # Special setup for the 7th call
        special_function = MagicMock(
            arguments='{\n  "subject": "ENGL",\n  "season_code": "202403",\n  "areas": "Hu",\n  "skills": "WR"\n}',
            name="CourseFilter",
        )
        special_tool_call = MagicMock(
            id="call_XwZ68clbWJGtafNAlM2uq9f0",
            function=special_function,
            type="function",
        )

        special_message = MagicMock(
            content=None,
            role="assistant",
            function_call=None,
            tool_calls=[special_tool_call],
        )
        special_choice = MagicMock(
            finish_reason="tool_calls", index=0, logprobs=None, message=special_message
        )

        special_chat_completion = MagicMock(
            id="chatcmpl-9EU2H7bduxQysddvkIYnJBFuq1gmR",
            choices=[special_choice],
            created=1713239077,
            model="gpt-4-0613",
            object="chat.completion",
            system_fingerprint=None,
            usage=MagicMock(
                completion_tokens=39, prompt_tokens=1475, total_tokens=1514
            ),
        )

        # Wrap these into the respective choice structures
        responses = [
            MagicMock(choices=[MagicMock(message=message_mock_with_tool_calls)]),
            MagicMock(choices=[MagicMock(message=message_mock_with_tool_calls)]),
            MagicMock(choices=[MagicMock(message=message_mock_with_tool_calls)]),
            special_chat_completion,
            MagicMock(choices=[MagicMock(message=message_mock_with_tool_calls)]),
            special_chat_completion,
        ]

        mock.side_effect = responses
        yield mock
```
```python
def test_with_frontend_filters(client, mock_chat_completion_complete):
    request_data = {
        "season_codes": ["bruh"],
        "subject": ["bruh"],
        "areas": ["WR", "Hu"],
        "message": [
            {"id": 123, "role": "user", "content": "msg"},
            {"id": 123, "role": "ai", "content": "msg2"},
            {"id": 123, "role": "user", "content": "Tell me about cs courses"},
        ],
    }
    response = client.post("/api/chat", json=request_data)
    assert response.status_code == 200
    data = response.get_json()
    assert "yes" in data["response"]
    assert mock_chat_completion_complete.call_count == 5
```
