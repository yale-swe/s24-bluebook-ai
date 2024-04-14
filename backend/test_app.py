import pytest
from unittest.mock import patch, MagicMock
from app import create_app


@pytest.fixture
def client():
    mock_collection = MagicMock()
    mock_collection.aggregate.return_value = iter(
        [
            {
                "course_code": "CS101",
                "title": "Intro to Computer Science",
                "description": "An introductory course.",
                "areas": ["Computer Science"],
            }
        ]
    )

    app = create_app({"TESTING": True, "collection": mock_collection})
    with app.test_client() as client:
        yield client


@pytest.fixture
def mock_chat_completion():
    # Ensure we're patching 'chat_completion_request' where it is imported/used in the Flask app
    with patch("app.chat_completion_request") as mock:
        mock.return_value = MagicMock(
            choices=[
                MagicMock(
                    message=MagicMock(content="Mock response based on user message")
                )
            ]
        )
        yield mock


def test_chat_endpoint(client, mock_chat_completion):
    request_data = {
        "message": [{"id": 123, "role": "user", "content": "Tell me about CS courses."}]
    }
    response = client.post("/api/chat", json=request_data)
    assert response.status_code == 200
    data = response.get_json()
    assert "Mock response based on user message" in data["response"]
    mock_chat_completion.assert_called_once()


def test_chat_endpoint_handles_api_error(client, mock_chat_completion):
    # Simulate an API error by having the mock raise an exception
    mock_chat_completion.side_effect = Exception("API error simulated")
    request_data = {
        "message": [{"id": 123, "role": "user", "content": "Error scenario test."}]
    }
    with pytest.raises(Exception):
        client.post("/api/chat", json=request_data)
