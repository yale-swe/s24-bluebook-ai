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
