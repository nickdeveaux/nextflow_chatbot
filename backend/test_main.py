"""
Minimal smoke tests for the Nextflow Chat Assistant backend.
Run with: pytest test_main.py -v
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from main import app


@pytest.fixture
def client():
    """Create test client fixture."""
    return TestClient(app)


@pytest.fixture
def mock_llm_client():
    """Mock LLM client to avoid real API calls in tests."""
    with patch('main.LLMClient') as mock:
        mock_instance = MagicMock()
        mock_instance.complete = MagicMock(return_value="This is a test response about Nextflow.")
        mock.return_value = mock_instance
        yield mock_instance


def test_health_endpoint(client):
    """Test the health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_chat_endpoint_basic(client, mock_llm_client):
    """Test basic chat endpoint functionality."""
    response = client.post(
        "/chat",
        json={"message": "What is Nextflow?"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "reply" in data
    assert "session_id" in data
    assert isinstance(data["reply"], str)
    assert len(data["reply"]) > 0


def test_chat_endpoint_with_session(client, mock_llm_client):
    """Test chat endpoint maintains session context."""
    # First message
    response1 = client.post(
        "/chat",
        json={"message": "What is the latest version of Nextflow?"}
    )
    assert response1.status_code == 200
    data1 = response1.json()
    session_id = data1["session_id"]
    
    # Follow-up message in same session
    response2 = client.post(
        "/chat",
        json={
            "message": "What was that version again?",
            "session_id": session_id
        }
    )
    assert response2.status_code == 200
    data2 = response2.json()
    assert data2["session_id"] == session_id
    assert "reply" in data2

def test_chat_endpoint_empty_message(client):
    """Test chat endpoint handles empty messages."""
    response = client.post(
        "/chat",
        json={"message": ""}
    )
    assert response.status_code in [400, 422]

