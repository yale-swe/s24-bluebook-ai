import pytest
from unittest.mock import patch, MagicMock
from app import create_app
from flask_testing import TestCase
from requests_mock import Mocker


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
    assert "collection" in app.config


@pytest.fixture
def client():
    mock_collection = MagicMock()
    mock_collection.aggregate.return_value = iter(
        [
            {
                "areas": ["Hu"],
                "course_code": "CPSC 150",
                "description": "Introduction to the basic ideas of computer science (computability, algorithm, virtual machine, symbol processing system), and of several ongoing relationships between computer science and other fields, particularly philosophy of mind.",
                "season_code": "202303",
                "sentiment_label": "NEGATIVE",
                "sentiment_score": 0.9444444444444444,
                "title": "Computer Science and the Modern Intellectual Agenda",
            },
        ]
    )

    app = create_app(
        {
            "TESTING": True,
            "collection": mock_collection,
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
    mock_collection = MagicMock()
    mock_collection.aggregate.return_value = iter(
        [
            {
                "areas": ["Hu"],
                "course_code": "CPSC 150",
                "description": "Introduction to the basic ideas of computer science (computability, algorithm, virtual machine, symbol processing system), and of several ongoing relationships between computer science and other fields, particularly philosophy of mind.",
                "season_code": "202303",
                "sentiment_label": "NEGATIVE",
                "sentiment_score": 0.9444444444444444,
                "title": "Computer Science and the Modern Intellectual Agenda",
            },
        ]
    )

    app = create_app(
        {
            "TESTING": True,
            "collection": mock_collection,
        }
    )
    with app.test_client() as client:
        yield client


@pytest.fixture
def mock_chat_completion_yes_no():
    with patch("app.chat_completion_request") as mock:
        # List of responses, one for each expected call
        responses = [
            MagicMock(choices=[MagicMock(message=MagicMock(content="yes"))]),
            MagicMock(choices=[MagicMock(message=MagicMock(content="no"))]),
            MagicMock(
                choices=[MagicMock(message=MagicMock(content="no need for query"))]
            ),
        ]
        mock.side_effect = responses
        yield mock


@pytest.fixture
def mock_chat_completion_no():
    with patch("app.chat_completion_request") as mock:
        # List of responses, one for each expected call
        responses = [
            MagicMock(choices=[MagicMock(message=MagicMock(content="no"))]),
            MagicMock(choices=[MagicMock(message=MagicMock(content="no"))]),
            MagicMock(
                choices=[
                    MagicMock(
                        message=MagicMock(content="Mock response based on user message")
                    )
                ]
            ),
        ]
        mock.side_effect = responses
        yield mock


@pytest.fixture
def mock_chat_completion_yes_yes():
    with patch("app.chat_completion_request") as mock:
        # List of responses, one for each expected call
        responses = [
            MagicMock(choices=[MagicMock(message=MagicMock(content="yes"))]),
            MagicMock(choices=[MagicMock(message=MagicMock(content="yes"))]),
            MagicMock(
                choices=[MagicMock(message=MagicMock(content="no need for query"))]
            ),
            MagicMock(
                choices=[
                    MagicMock(
                        message=MagicMock(content="Mock response based on user message")
                    )
                ]
            ),
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
    assert mock_chat_completion_yes_yes.call_count == 4


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
            MagicMock(message=MagicMock(content="Mock response based on user message"))
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
    assert mock_chat_completion_yes_yes.call_count == 4


def test_api_error(client, mock_chat_completion_yes_no):
    # Simulate an API error by having the mock raise an exception
    mock_chat_completion_yes_no.side_effect = Exception("API error simulated")
    request_data = {
        "message": [{"id": 123, "role": "user", "content": "Error scenario test."}]
    }
    with pytest.raises(Exception):
        client.post("/api/chat", json=request_data)
