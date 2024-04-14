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


@patch("app.MongoClient")  # Mock the entire MongoClient to avoid any real DB calls
def test_chat_endpoint(mock_mongo_client, client):
    # Mock database and collection
    mock_db = mock_mongo_client.return_value
    mock_collection = mock_db.test_db.parsed_courses
    mock_collection.aggregate.return_value = [
        {
            "course_code": "CS101",
            "title": "Intro to CS",
            "description": "Basics of programming.",
            "areas": ["CS"],
        }
    ]

    # Setup the mock for the chat completion request to simulate OpenAI response
    with patch("app.chat_completion_request") as mock_chat_completion_request:
        mock_chat_completion_request.return_value.choices = [
            MagicMock(message=MagicMock(content="Here's your response"))
        ]

        # Setup the mock for the create embedding
        with patch("app.create_embedding") as mock_create_embedding:
            mock_create_embedding.return_value = [
                0.1
            ] * 1536  # Assume 1536-dimensional embedding

            # Simulate a POST request to the chat endpoint
            response = client.post(
                "/api/chat",
                json={
                    "message": [{"role": "user", "content": "Tell me about CS courses"}]
                },
            )

            # Check if the response is correct
            assert response.status_code == 200
            response_data = json.loads(response.data.decode("utf-8"))
            assert "courses" in response_data
            assert response_data["response"] == "Here's your response"
            assert (
                len(response_data["courses"]) == 5
            )  # Make sure this matches the expected number of courses


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
