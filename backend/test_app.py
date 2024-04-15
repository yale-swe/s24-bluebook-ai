import pytest
from unittest.mock import patch, MagicMock
from app import create_app


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
                "sentiment_info": {
                    "final_label": "NEGATIVE",
                    "final_proportion": 0.9444444444444444,
                },
                "title": "Computer Science and the Modern Intellectual Agenda",
            },
        ]
    )

    app = create_app({"TESTING": True, "courses": mock_collection})
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
    assert mock_chat_completion.call_count == 2


def test_chat_endpoint_handles_api_error(client, mock_chat_completion):
    # Simulate an API error by having the mock raise an exception
    mock_chat_completion.side_effect = Exception("API error simulated")
    request_data = {
        "message": [{"id": 123, "role": "user", "content": "Error scenario test."}]
    }
    with pytest.raises(Exception):
        client.post("/api/chat", json=request_data)
