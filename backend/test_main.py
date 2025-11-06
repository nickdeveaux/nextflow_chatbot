"""
Tests for the Nextflow Chat Assistant backend.
Run with: pytest test_main.py -v
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock, MagicMock
from main import app
import os


@pytest.fixture
def client():
    """Create test client fixture."""
    return TestClient(app)


@pytest.fixture
def mock_llm_client():
    """Mock LLM client to avoid real API calls in tests."""
    with patch('main.LLMClient') as mock:
        mock_instance = MagicMock()
        # complete is now synchronous
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

def test_chat_endpoint_citations(client, mock_llm_client):
    """Test that citations are returned when available."""
    response = client.post(
        "/chat",
        json={"message": "What is Nextflow?"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "citations" in data
    # Citations may be None or a list
    if data["citations"] is not None:
        assert isinstance(data["citations"], list)
        assert len(data["citations"]) > 0

def test_chat_endpoint_empty_message(client):
    """Test chat endpoint handles empty messages."""
    response = client.post(
        "/chat",
        json={"message": ""}
    )
    # Should still process, but may return empty or error
    assert response.status_code in [200, 400, 422]

def test_chat_endpoint_dsl2_question(client, mock_llm_client):
    """Test chat endpoint with DSL2 syntax question."""
    response = client.post(
        "/chat",
        json={"message": "Are from and into parts of DSL2 syntax?"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "reply" in data
    assert len(data["reply"]) > 0

def test_chat_endpoint_executor_question(client, mock_llm_client):
    """Test chat endpoint with executor question."""
    response = client.post(
        "/chat",
        json={"message": "Does Nextflow support a Moab executor?"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "reply" in data
    assert len(data["reply"]) > 0

@pytest.mark.asyncio
async def test_get_knowledge_context():
    """Test knowledge context retrieval."""
    from main import get_knowledge_context
    
    # Test with a query
    context = get_knowledge_context("What is Nextflow?")
    # Context may be empty if vector store not initialized, which is OK
    assert isinstance(context, str)

def test_chat_response_structure(client, mock_llm_client):
    """Test that chat response has correct structure."""
    response = client.post(
        "/chat",
        json={"message": "Hello"}
    )
    assert response.status_code == 200
    data = response.json()
    
    # Check required fields
    assert "reply" in data
    assert "session_id" in data
    assert isinstance(data["reply"], str)
    assert isinstance(data["session_id"], str)
    assert len(data["reply"]) > 0
    assert len(data["session_id"]) > 0
    
    # Check optional fields
    if "citations" in data:
        assert data["citations"] is None or isinstance(data["citations"], list)
        if data["citations"]:
            for citation in data["citations"]:
                assert isinstance(citation, str)
                assert citation.startswith("http")


def test_chat_endpoint_with_citations_request(client, mock_llm_client):
    """Test citations are returned when requested."""
    response = client.post(
        "/chat",
        json={"message": "Can you cite that?"}
    )
    assert response.status_code == 200
    data = response.json()
    # Citations may or may not be present depending on vector store
    if data.get("citations"):
        assert isinstance(data["citations"], list)

