from flask_testing import TestCase
from app import app
from unittest.mock import patch, MagicMock
import json
import pytest


@pytest.fixture
def client():
    app.config["TESTING"] = True
    app.config["DATABASE_URI"] = "mongodb://test:test@localhost/test_db"

    # Setup other necessary configuration like secret keys or disable CSRF if needed

    with app.test_client() as client:
        yield client


@patch("app.requests.get")  # Mocking requests.get used in the CAS validation
@patch("app.chat_completion_request")  # Mocking the OpenAI call
@patch("app.create_embedding")  # Mocking the embedding creation
@patch("app.MongoClient")  # Mock the MongoDB client
def test_chat_endpoint(
    mock_mongo_client,
    mock_create_embedding,
    mock_chat_completion_request,
    mock_get,
    client,
):
    # Setup MongoDB mock
    mock_db = mock_mongo_client.return_value.__getitem__.return_value
    mock_collection = mock_db.__getitem__.return_value
    mock_collection.aggregate.return_value = [
        {
            "course_code": "CS101",
            "title": "Intro to CS",
            "description": "Basics of programming.",
            "areas": ["CS"],
        }
    ]

    # Setup embedding mock
    mock_create_embedding.return_value = []
    for i in range(1, 1537):
        mock_create_embedding.return_value.append(float("0." + str(i)))

    # Setup OpenAI chat mock
    mock_chat_completion_request.return_value.choices = [
        MagicMock(message=MagicMock(content="Here's your response"))
    ]

    # Simulate a post request to the chat endpoint
    response = client.post(
        "/api/chat",
        json={"message": [{"role": "user", "content": "Tell me about CS courses"}]},
    )

    # Check if the response is correct
    assert response.status_code == 200
    response_data = json.loads(response.data.decode("utf-8"))
    assert "courses" in response_data
    assert response_data["response"] == "Here's your response"
    assert len(response_data["courses"]) == 5


class TestCASAuthentication(TestCase):
    def create_app(self):
        app.config["TESTING"] = True
        app.config["DATABASE_URI"] = "mongodb://test:test@localhost/test_db"
        return app

    @patch("requests.get")
    def test_validate_cas_ticket(self, mock_get):
        mock_response = mock_get.return_value
        mock_response.status_code = 200
        mock_response.content = b"<cas:serviceResponse xmlns:cas='http://www.yale.edu/tp/cas'><cas:authenticationSuccess><cas:user>testuser</cas:user></cas:authenticationSuccess></cas:serviceResponse>"

        response = self.client.post(
            "/validate_ticket",
            data=json.dumps({"ticket": "fake-ticket", "service_url": "fake-url"}),
            content_type="application/json",
        )
        data = response.get_json()
        self.assertTrue(data["isAuthenticated"])
