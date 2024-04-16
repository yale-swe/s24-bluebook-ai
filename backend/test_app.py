from uuid import uuid4
import pytest
from unittest.mock import patch, MagicMock
from app import create_app
from flask_testing import TestCase
from requests_mock import Mocker
import json


# Define the TestConfig as a dictionary directly
test_config = {
    "TESTING": True,
    "CAS_SERVER": "https://secure.its.yale.edu/cas",
    "FLASK_SECRET_KEY": "test_secret",
    "MONGO_URI": "mongodb://localhost:27017/test",
}


class TestApp(TestCase):
    def create_app(self):
        # Create an app using the test configuration dictionary
        return create_app(test_config)

    def test_login_route(self):
        response = self.client.get("/login")
        # Directly specify the expected redirection URL
        self.assertEqual(response.headers["Location"], "/login/")

    def test_logout_route(self):
        response = self.client.get("/logout")
        # Directly specify the expected redirection URL
        self.assertEqual(response.headers["Location"], "/logout/")

    def test_route_after_login(self):
        with self.client.session_transaction() as sess:
            sess["CAS_USERNAME"] = "testuser"

        response = self.client.get("/route_after_login")
        self.assertEqual(response.status_code, 200)
        self.assertIn("Logged in as testuser", response.data.decode())

    @Mocker()
    def test_validate_ticket_failure_authentication(self, m):
        # Mock the CAS server response to simulate authentication failure
        cas_response_xml = """
        <cas:serviceResponse xmlns:cas="http://www.yale.edu/tp/cas">
            <cas:authenticationFailure code="INVALID_TICKET">
                "Ticket ST-12345 not recognized"
            </cas:authenticationFailure>
        </cas:serviceResponse>
        """
        cas_validate_url = "https://secure.its.yale.edu/cas/serviceValidate"
        m.get(
            cas_validate_url, text=cas_response_xml, status_code=200
        )  # CAS often uses 200 OK even for failed authentication responses

        # Make a POST request to the validate_ticket route with mock data
        data = {"ticket": "ST-12345", "service_url": "http://localhost:5000"}
        response = self.client.post("/validate_ticket", json=data)
        self.assertEqual(response.status_code, 401)
        self.assertFalse(
            response.json["isAuthenticated"], "Expected authentication to fail"
        )

    @Mocker()
    def test_validate_ticket_success(self, m):
        m.get(
            "https://secure.its.yale.edu/cas/serviceValidate",
            text='<cas:serviceResponse xmlns:cas="http://www.yale.edu/tp/cas"><cas:authenticationSuccess><cas:user>testuser</cas:user></cas:authenticationSuccess></cas:serviceResponse>',
        )
        data = {"ticket": "ST-12345", "service_url": "http://localhost:5000"}
        response = self.client.post("/validate_ticket", json=data)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(
            "isAuthenticated" in response.json and response.json["isAuthenticated"]
        )

    @Mocker()
    def test_validate_ticket_failure(self, m):
        m.get("https://secure.its.yale.edu/cas/serviceValidate", status_code=401)
        data = {"ticket": "ST-12345", "service_url": "http://localhost:5000"}
        response = self.client.post("/validate_ticket", json=data)
        self.assertEqual(response.status_code, 401)
        self.assertFalse(
            "isAuthenticated" in response.json and response.json["isAuthenticated"]
        )

    def test_validate_ticket_no_data(self):
        response = self.client.post("/validate_ticket", json={})
        self.assertEqual(response.status_code, 400)
        self.assertIn("Ticket or service URL not provided", response.json["error"])


@pytest.fixture
def app():
    app = create_app(test_config)
    return app


def test_load_config_with_test_config(app):
    assert app.secret_key == "test_secret"
    assert app.config["CAS_SERVER"] == "https://secure.its.yale.edu/cas"


def test_init_database_with_config(app):
    assert "courses" in app.config


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


@pytest.fixture
def client_all_disabled():
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
        }
    )
    with app.test_client() as client:
        yield client


@pytest.fixture
def mock_chat_completion_yes_no():
    with patch("app.chat_completion_request") as mock:
        # List of responses, one for each expected call
        responses = [
            MagicMock(
                choices=[
                    MagicMock(
                        message=MagicMock(
                            content="yes",
                            tool_calls=[
                                MagicMock(
                                    function=MagicMock(
                                        arguments='{\n "season_code": "202303"\n}'
                                    )
                                )
                            ],
                        )
                    )
                ]
            ),
            MagicMock(
                choices=[
                    MagicMock(
                        message=MagicMock(
                            content="no",
                            tool_calls=[
                                MagicMock(
                                    function=MagicMock(
                                        arguments='{\n "season_code": "202303"\n}'
                                    )
                                )
                            ],
                        )
                    )
                ]
            ),
            MagicMock(
                choices=[
                    MagicMock(
                        message=MagicMock(
                            content="no need for query",
                            tool_calls=[
                                MagicMock(
                                    function=MagicMock(
                                        arguments='{\n "season_code": "202303"\n}'
                                    )
                                )
                            ],
                        )
                    )
                ]
            ),
        ]
        mock.side_effect = responses
        yield mock


@pytest.fixture
def mock_chat_completion_no():
    with patch("app.chat_completion_request") as mock:
        # List of responses, each with the expected structure
        responses = [
            MagicMock(
                choices=[
                    MagicMock(
                        message=MagicMock(
                            content="no",
                            tool_calls=[
                                MagicMock(
                                    function=MagicMock(
                                        arguments='{"season_code": "202303"}'
                                    )
                                )
                            ],
                        )
                    )
                ]
            )
            for _ in range(3)
        ]
        mock.side_effect = responses
        yield mock


@pytest.fixture
def mock_chat_completion_yes_yes():
    with patch("app.chat_completion_request") as mock:
        # Prepare the function mock that includes tool calls with the arguments JSON string
        function_mock = MagicMock()
        function_mock.arguments = '{"season_code": "202303"}'

        # Mock for tool_calls that uses the prepared function mock
        tool_call_mock = MagicMock()
        tool_call_mock.function = function_mock

        # Mock for the message that includes the list of tool calls
        message_mock_with_tool_calls = MagicMock()
        message_mock_with_tool_calls.content = "yes"
        message_mock_with_tool_calls.tool_calls = [tool_call_mock]

        message_mock_mock_response = MagicMock()
        message_mock_mock_response.content = "Mock response based on user message"
        message_mock_mock_response.tool_calls = [tool_call_mock]

        # Wrap these into the respective choice structures
        responses = [
            MagicMock(choices=[MagicMock(message=message_mock_with_tool_calls)]),
            MagicMock(choices=[MagicMock(message=message_mock_with_tool_calls)]),
            MagicMock(choices=[MagicMock(message=message_mock_with_tool_calls)]),
            MagicMock(choices=[MagicMock(message=message_mock_with_tool_calls)]),
            MagicMock(choices=[MagicMock(message=message_mock_mock_response)]),
        ]

        mock.side_effect = responses
        yield mock


def test_chat_endpoint(client, mock_chat_completion_yes_yes):
    request_data = {
        "message": [
            {"id": 123, "role": "user", "content": "msg"},
            {"id": 123, "role": "ai", "content": "msg2"},
            {"id": 123, "role": "user", "content": "Tell me about cs courses"},
        ]
    }
    response = client.post("/api/chat", json=request_data)
    assert response.status_code == 200
    data = response.get_json()
    assert "Mock response based on user message" in data["response"]
    assert mock_chat_completion_yes_yes.call_count == 5


def test_no_need_for_query(client, mock_chat_completion_yes_no):
    request_data = {
        "message": [
            {"id": 123, "role": "user", "content": "msg"},
            {"id": 123, "role": "ai", "content": "msg2"},
            {"id": 123, "role": "user", "content": "Tell me about cs courses"},
        ]
    }
    response = client.post("/api/chat", json=request_data)
    assert response.status_code == 200
    data = response.get_json()
    assert "no need for query" in data["response"]
    assert mock_chat_completion_yes_no.call_count == 3


@pytest.fixture
def mock_chat_completion_complete():
    with patch("app.chat_completion_request") as mock:
        # Prepare the function mock that includes tool calls with the arguments JSON string
        function_mock = MagicMock()
        function_mock.arguments = '{"season_code": "202303"}'

        # Mock for tool_calls that uses the prepared function mock
        tool_call_mock = MagicMock()
        tool_call_mock.function = function_mock

        # Mock for the message that includes the list of tool calls
        message_mock_with_tool_calls = MagicMock()
        message_mock_with_tool_calls.content = "yes"
        message_mock_with_tool_calls.tool_calls = [tool_call_mock]

        message_mock_mock_response = MagicMock()
        message_mock_mock_response.content = "Mock response based on user message"
        message_mock_mock_response.tool_calls = [tool_call_mock]

        # Wrap these into the respective choice structures
        responses = [
            MagicMock(choices=[MagicMock(message=message_mock_with_tool_calls)]),
            MagicMock(choices=[MagicMock(message=message_mock_with_tool_calls)]),
            MagicMock(choices=[MagicMock(message=message_mock_with_tool_calls)]),
            MagicMock(choices=[MagicMock(message=message_mock_with_tool_calls)]),
            MagicMock(choices=[MagicMock(message=message_mock_mock_response)]),
            MagicMock(choices=[MagicMock(message=message_mock_mock_response)]),
            MagicMock(choices=[MagicMock(message=message_mock_mock_response)]),
            MagicMock(choices=[MagicMock(message=message_mock_mock_response)]),
            MagicMock(choices=[MagicMock(message=message_mock_mock_response)]),
            MagicMock(choices=[MagicMock(message=message_mock_mock_response)]),
            MagicMock(choices=[MagicMock(message=message_mock_mock_response)]),
        ]

        mock.side_effect = responses
        yield mock


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
    assert "Mock response based on user message" in data["response"]
    assert mock_chat_completion_complete.call_count == 5


def test_no_user_message(client, mock_chat_completion_complete):
    request_data = {
        "season_codes": ["bruh"],
        "subject": ["bruh"],
        "areas": ["WR", "Hu"],
    }
    response = client.post("/api/chat", json=request_data)
    assert response.status_code == 200
    data = response.get_json()
    assert "No message provided" in data["error"]
    assert mock_chat_completion_complete.call_count == 0


def test_safty_violation(client, mock_chat_completion_no):
    request_data = {
        "message": [
            {"id": 123, "role": "user", "content": "msg"},
            {"id": 123, "role": "ai", "content": "msg2"},
            {"id": 123, "role": "user", "content": "Tell me about cs courses"},
        ]
    }
    response = client.post("/api/chat", json=request_data)
    assert response.status_code == 200
    data = response.get_json()
    assert "I am sorry" in data["response"]
    assert mock_chat_completion_no.call_count == 1


def test_all_disable(client_all_disabled, mock_chat_completion_yes_yes):
    client = client_all_disabled
    mock_chat_completion_yes_yes.return_value = MagicMock(
        choices=[
            MagicMock(
                message=MagicMock(
                    content="no",
                    tool_calls=[
                        MagicMock(
                            function=MagicMock(
                                arguments='{\n "season_code": "202303"\n}'
                            )
                        )
                    ],
                )
            )
        ]
    )
    request_data = {
        "message": [
            {"id": 123, "role": "user", "content": "msg"},
            {"id": 123, "role": "ai", "content": "msg2"},
            {"id": 123, "role": "user", "content": "Tell me about cs courses"},
        ]
    }
    response = client.post("/api/chat", json=request_data)
    assert response.status_code == 200
    data = response.get_json()
    assert "Mock response based on user message" in data["response"]
    assert mock_chat_completion_yes_yes.call_count == 5


def test_api_error(client, mock_chat_completion_yes_no):
    # Simulate an API error by having the mock raise an exception
    mock_chat_completion_yes_no.side_effect = Exception("API error simulated")
    request_data = {
        "message": [{"id": 123, "role": "user", "content": "Error scenario test."}]
    }
    with pytest.raises(Exception):
        client.post("/api/chat", json=request_data)


# test save


def test_save_chat_success(client):
    client.application.config["courses"].insert_one.return_value = MagicMock(
        inserted_id="123456"
    )
    response = client.post("/api/save_chat", json={"message": "Hello, world!"})
    assert response.status_code == 201
    assert json.loads(response.data) == {"status": "success", "id": "123456"}


def test_save_chat_failure(client):
    client.application.config["courses"].insert_one.side_effect = Exception(
        "Failed to insert"
    )
    response = client.post("/api/save_chat", json={"message": "Hello, world!"})
    assert response.status_code == 500
    assert json.loads(response.data) == {
        "status": "error",
        "message": "Failed to insert",
    }


# test reload


def test_reload_chat_found(client):
    client.application.config["courses"].find_one.return_value = {
        "_id": "123456",
        "message": "Hello, test!",
    }
    response = client.post("/api/reload_chat", json={"chat_id": "123456"})
    assert response.status_code == 200
    assert json.loads(response.data) == {
        "status": "success",
        "chat": {"_id": "123456", "message": "Hello, test!"},
    }


def test_reload_chat_not_found(client):
    client.application.config["courses"].find_one.return_value = None
    response = client.post("/api/reload_chat", json={"chat_id": "nonexistent"})
    assert response.status_code == 404
    assert json.loads(response.data) == {"status": "not found"}


def test_reload_chat_exception(client):
    client.application.config["courses"].find_one.side_effect = Exception(
        "Database error"
    )
    response = client.post("/api/reload_chat", json={"chat_id": "123456"})
    assert response.status_code == 500
    assert json.loads(response.data) == {"status": "error", "message": "Database error"}


# test verify course code


# Test case when no UID is provided
def test_verify_course_code_no_uid_provided(client):
    response = client.post("/api/verify_course_code", json={})
    assert response.status_code == 400
    assert json.loads(response.data) == {"error": "No uid provided"}


# Test case when the course code exists
def test_verify_course_code_exists(client):
    client.application.config["courses"].find_one.return_value = {
        "course_code": "CPSC 150"
    }
    client.application.config["profiles"].update_one.return_value = MagicMock(
        acknowledged=True
    )
    response = client.post(
        "/api/verify_course_code", json={"uid": "user123", "search": "CPSC 150"}
    )
    assert response.status_code == 200
    assert json.loads(response.data) == {"status": "success", "course": "CPSC 150"}


# Test case when the course code does not exist
def test_verify_course_code_not_exist(client):
    client.application.config["courses"].find_one.return_value = None
    response = client.post(
        "/api/verify_course_code", json={"uid": "user123", "search": "CPSC 150"}
    )
    assert response.status_code == 404
    assert json.loads(response.data) == {"status": "invalid course code"}


# Test case for exception during database operation
def test_verify_course_code_exception(client):
    client.application.config["courses"].find_one.side_effect = Exception(
        "Database error"
    )
    response = client.post(
        "/api/verify_course_code", json={"uid": "user123", "search": "CPSC 150"}
    )
    assert response.status_code == 500
    assert json.loads(response.data) == {"status": "error", "message": "Database error"}


# test delete course code


def test_delete_course_code_no_uid_provided(client):
    response = client.post("/api/delete_course_code", json={})
    assert response.status_code == 400
    assert response.get_json() == {"error": "No uid provided"}


def test_delete_course_code_exists(client):
    # Mock find_one to return a course
    client.application.config["courses"].find_one.return_value = {
        "course_code": "CPSC 150"
    }
    # Mock update_one to simulate successful removal
    client.application.config["profiles"].update_one.return_value = MagicMock(
        acknowledged=True
    )

    response = client.post(
        "/api/delete_course_code", json={"uid": "user123", "search": "CPSC 150"}
    )
    assert response.status_code == 200
    assert response.get_json() == {"status": "success", "course": "CPSC 150"}


def test_delete_course_code_not_exist(client):
    # Mock find_one to return None, indicating no course found
    client.application.config["courses"].find_one.return_value = None

    response = client.post(
        "/api/delete_course_code", json={"uid": "user123", "search": "CPSC 150"}
    )
    assert response.status_code == 404
    assert response.get_json() == {"status": "invalid course code"}


def test_delete_course_code_exception(client):
    # Simulate an exception when attempting to find a course
    client.application.config["courses"].find_one.side_effect = Exception(
        "Database error"
    )

    response = client.post(
        "/api/delete_course_code", json={"uid": "user123", "search": "CPSC 150"}
    )
    assert response.status_code == 500
    assert response.get_json() == {"status": "error", "message": "Database error"}


# test create user


def test_create_user_no_uid_provided(client):
    response = client.post("/api/user/create", json={})
    assert (
        response.status_code == 200
    )  # Assuming a 200 OK with an error message in your setup
    assert response.get_json() == {"error": "No uid provided"}


def test_create_user_successful(client):
    # Mock the insert_one operation
    client.application.config["profiles"].insert_one.return_value = MagicMock(
        inserted_id="mock_id"
    )
    response = client.post("/api/user/create", json={"uid": "user123"})
    expected_profile = {
        "_id": "mock_id",
        "uid": "user123",
        "chat_history": [],
        "courses": [],
        "name": "",
    }
    assert response.status_code == 200
    assert response.get_json() == expected_profile


# test get user profile


def test_get_user_profile_no_uid_provided(client):
    response = client.post("/api/user/profile", json={})
    assert (
        response.status_code == 200
    )  # Assuming a 200 OK with an error message in your setup
    assert response.get_json() == {"error": "No uid provided"}


def test_get_user_profile_not_found(client):
    # Mock find_one to return None
    client.application.config["profiles"].find_one.return_value = None
    response = client.post("/api/user/profile", json={"uid": "nonexistent"})
    assert response.status_code == 404
    assert response.get_json() == {"error": "No user profile found"}


def test_get_user_profile_successful(client):
    # Mock find_one to return a profile
    mock_profile = {
        "_id": "mock_id",
        "uid": "user123",
        "chat_history": [],
        "courses": [],
        "name": "Test User",
    }
    client.application.config["profiles"].find_one.return_value = mock_profile
    response = client.post("/api/user/profile", json={"uid": "user123"})
    expected_profile = {
        "_id": "mock_id",
        "uid": "user123",
        "chat_history": [],
        "courses": [],
        "name": "Test User",
    }
    assert response.status_code == 200
    assert response.get_json() == expected_profile


# test update user name


def test_update_user_name_no_uid_provided(client):
    response = client.post("/api/user/update/name", json={})
    assert response.status_code == 200  # Assuming a 200 OK with error message
    assert response.get_json() == {"error": "No uid provided"}


def test_update_user_name_no_name_provided(client):
    response = client.post("/api/user/update/name", json={"uid": "user123"})
    assert response.status_code == 200  # Assuming a 200 OK with error message
    assert response.get_json() == {"error": "No name provided"}


def test_update_user_name_successful(client):
    # Setup mock to return a valid user profile initially and after update
    client.application.config["profiles"].find_one.side_effect = [
        {"_id": "mock_id", "uid": "user123", "name": ""},
        {"_id": "mock_id", "uid": "user123", "name": "New Name"},
    ]
    client.application.config["profiles"].update_one.return_value = MagicMock(
        acknowledged=True
    )
    response = client.post(
        "/api/user/update/name", json={"uid": "user123", "name": "New Name"}
    )
    assert response.status_code == 200
    assert response.get_json() == {
        "_id": "mock_id",
        "uid": "user123",
        "name": "New Name",
    }


# test create chat


@patch("uuid.uuid4", return_value=uuid4())
def test_create_chat_no_uid_provided(mock_uuid, client):
    response = client.post("/api/chat/create_chat", json={})
    assert response.status_code == 200  # Assuming a 200 OK with error message
    assert response.get_json() == {"error": "No uid provided"}


@patch("uuid.uuid4", return_value=uuid4())
def test_create_chat_with_message(mock_uuid, client):
    client.application.config["profiles"].update_one.return_value = MagicMock(
        acknowledged=True
    )
    response = client.post(
        "/api/chat/create_chat", json={"uid": "user123", "message": "Hello!"}
    )
    assert response.status_code == 200
    assert response.get_json() == {"status": "success"}


@patch("uuid.uuid4", return_value=uuid4())
def test_create_chat_without_message(mock_uuid, client):
    client.application.config["profiles"].update_one.return_value = MagicMock(
        acknowledged=True
    )
    response = client.post("/api/chat/create_chat", json={"uid": "user123"})
    assert response.status_code == 200
    assert response.get_json() == {"status": "success"}


# test append message


def test_append_message_no_uid_provided(client):
    response = client.post(
        "/api/chat/append_message", json={"chat_id": "chat123", "message": "Hello!"}
    )
    assert response.status_code == 200
    assert response.get_json() == {"error": "No uid provided"}


def test_append_message_no_message_provided(client):
    response = client.post(
        "/api/chat/append_message", json={"uid": "user123", "chat_id": "chat123"}
    )
    assert response.status_code == 200
    assert response.get_json() == {"error": "No message provided"}


def test_append_message_no_chat_id_provided(client):
    response = client.post(
        "/api/chat/append_message", json={"uid": "user123", "message": "Hello!"}
    )
    assert response.status_code == 200
    assert response.get_json() == {"error": "No chat_id provided"}


def test_append_message_user_not_found(client):
    client.application.config["profiles"].find_one.return_value = None
    response = client.post(
        "/api/chat/append_message",
        json={"uid": "user123", "chat_id": "chat123", "message": "Hello!"},
    )
    assert response.status_code == 404
    assert response.get_json() == {"error": "No user profile found"}


def test_append_message_chat_not_found(client):
    # Setup mock to return a valid user profile but no matching chat
    client.application.config["profiles"].find_one.return_value = {
        "uid": "user123",
        "chat_history": [],
    }
    response = client.post(
        "/api/chat/append_message",
        json={"uid": "user123", "chat_id": "chat123", "message": "Hello!"},
    )
    assert response.status_code == 200
    assert (
        response.get_json() == {"status": "success"}
    )  # Chat not found but status is success, consider updating logic or test expectation


def test_append_message_successful(client):
    # Mock user profile with a specific chat to update
    client.application.config["profiles"].find_one.return_value = {
        "uid": "user123",
        "chat_history": [{"chat_id": "chat123", "messages": []}],
    }
    client.application.config["profiles"].update_one.return_value = MagicMock(
        acknowledged=True
    )
    response = client.post(
        "/api/chat/append_message",
        json={"uid": "user123", "chat_id": "chat123", "message": "Hello!"},
    )
    assert response.status_code == 200
    assert response.get_json() == {"status": "success"}


# test delete chat


def test_delete_chat_no_uid_provided(client):
    response = client.post("/api/chat/delete_chat", json={"chat_id": "chat123"})
    assert response.status_code == 200
    assert response.get_json() == {"error": "No uid provided"}


def test_delete_chat_no_chat_id_provided(client):
    response = client.post("/api/chat/delete_chat", json={"uid": "user123"})
    assert response.status_code == 200
    assert response.get_json() == {"error": "No chat_id provided"}


def test_delete_chat_successful(client):
    client.application.config["profiles"].update_one.return_value = MagicMock(
        acknowledged=True
    )
    response = client.post(
        "/api/chat/delete_chat", json={"uid": "user123", "chat_id": "chat123"}
    )
    assert response.status_code == 200
    assert response.get_json() == {"status": "success"}


@pytest.fixture
def mock_chat_completion():
    with patch("app.chat_completion_request") as mock:
        mock.return_value = "what the hell is going on"
        yield mock


# test slug
# Test for a valid response from chat_completion_request
def test_get_chat_history_slug_valid_response(mock_chat_completion, client):
    # Setting up the mock to return a specific slug
    mock_chat_completion.return_value = MagicMock(
        choices=[MagicMock(message=MagicMock(content="Effective Slug"))]
    )
    message_data = {"message": [{"role": "user", "content": "Hello, world!"}]}
    response = client.post("/api/slug", json=message_data)
    assert response.status_code == 200
    assert response.get_json() == {"slug": "Effective Slug"}


# Test for handling failures or empty responses from chat_completion_request
def test_get_chat_history_slug_failure_handling(mock_chat_completion, client):
    # Simulate failure by not providing choices or content
    mock_chat_completion.return_value = MagicMock(choices=[])
    message_data = {"message": [{"role": "user", "content": "Hello, world!"}]}
    response = client.post("/api/slug", json=message_data)
    assert response.status_code == 200
    assert response.get_json() == {"slug": "Untitled"}
