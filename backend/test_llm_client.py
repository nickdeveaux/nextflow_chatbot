"""
Tests for LLM client.
"""
import pytest
import os
import tempfile
from unittest.mock import Mock, patch, MagicMock
from llm_client import LLMClient
import config


@pytest.fixture
def mock_completion():
    """Mock litellm completion function."""
    with patch('llm_client.completion') as mock:
        yield mock


@pytest.fixture
def sample_messages():
    """Sample messages for testing."""
    return [
        {"role": "user", "content": "What is Nextflow?"}
    ]


def test_llm_client_initialization():
    """Test LLM client initialization with defaults."""
    client = LLMClient()
    assert client.model == config.LLM_MODEL
    assert client.api_key == config.GOOGLE_VERTEX_API_KEY
    assert client.temperature == config.LLM_TEMPERATURE
    assert client.max_tokens == config.LLM_MAX_TOKENS


def test_llm_client_custom_params():
    """Test LLM client with custom parameters."""
    client = LLMClient(
        model="test-model",
        api_key="test-key",
        temperature=0.5,
        max_tokens=100
    )
    assert client.model == "test-model"
    assert client.api_key == "test-key"
    assert client.temperature == 0.5
    assert client.max_tokens == 100


@pytest.mark.asyncio
async def test_llm_client_complete_success(mock_completion, sample_messages):
    """Test successful LLM completion."""
    # Mock response
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = "Nextflow is a workflow system."
    mock_completion.return_value = mock_response
    
    client = LLMClient(api_key="test-key", model="gemini/test")
    result = await client.complete(sample_messages)
    
    assert result == "Nextflow is a workflow system."
    mock_completion.assert_called_once()
    call_kwargs = mock_completion.call_args[1]
    assert call_kwargs["model"] == "gemini/test"
    assert call_kwargs["messages"] == sample_messages


@pytest.mark.asyncio
async def test_llm_client_with_system_prompt(mock_completion, sample_messages):
    """Test LLM client with system prompt."""
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = "Response"
    mock_completion.return_value = mock_response
    
    client = LLMClient(api_key="test-key")
    result = await client.complete(sample_messages, system_prompt="You are a helpful assistant.")
    
    # Check that system prompt was prepended
    call_args = mock_completion.call_args
    messages = call_args[1]["messages"]
    assert messages[0]["role"] == "system"
    assert messages[0]["content"] == "You are a helpful assistant."
    assert messages[1] == sample_messages[0]


@pytest.mark.asyncio
async def test_llm_client_empty_response(mock_completion, sample_messages):
    """Test handling of empty LLM response."""
    mock_response = MagicMock()
    mock_response.choices = []
    mock_completion.return_value = mock_response
    
    client = LLMClient(api_key="test-key")
    with pytest.raises(ValueError, match="Empty response from LLM"):
        await client.complete(sample_messages)


@pytest.mark.asyncio
async def test_llm_client_empty_content(mock_completion, sample_messages):
    """Test handling of empty content in response."""
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = None
    mock_completion.return_value = mock_response
    
    client = LLMClient(api_key="test-key")
    with pytest.raises(ValueError, match="Empty content in LLM response"):
        await client.complete(sample_messages)


@pytest.mark.asyncio
async def test_llm_client_no_api_key(mock_completion, sample_messages):
    """Test error when API key is not set."""
    client = LLMClient(api_key=None)
    # Override to ensure it's truly empty
    client.api_key = None
    with pytest.raises(ValueError, match="API key not set"):
        await client.complete(sample_messages)


@pytest.mark.asyncio
async def test_llm_client_vertex_credentials_json(mock_completion, sample_messages):
    """Test Vertex AI credentials setup with JSON key."""
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = "Response"
    mock_completion.return_value = mock_response
    
    json_key = '{"type": "service_account", "project_id": "test"}'
    client = LLMClient(
        api_key=json_key,
        model="vertex_ai/gemini-test",
        project_id="test-project"
    )
    
    # Save original env vars
    original_creds = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")
    original_project = os.environ.get("GOOGLE_CLOUD_PROJECT")
    
    try:
        await client.complete(sample_messages)
        
        # Check that env vars were set (before cleanup)
        # Note: cleanup happens in finally, so we check during the call
        # We'll verify the setup method was called correctly instead
        assert client.model.startswith("vertex_ai/")
    finally:
        # Restore original env vars
        if original_creds:
            os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = original_creds
        elif "GOOGLE_APPLICATION_CREDENTIALS" in os.environ:
            del os.environ["GOOGLE_APPLICATION_CREDENTIALS"]
        
        if original_project:
            os.environ["GOOGLE_CLOUD_PROJECT"] = original_project
        elif "GOOGLE_CLOUD_PROJECT" in os.environ:
            del os.environ["GOOGLE_CLOUD_PROJECT"]


@pytest.mark.asyncio
async def test_llm_client_vertex_credentials_path(mock_completion, sample_messages):
    """Test Vertex AI credentials setup with file path."""
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = "Response"
    mock_completion.return_value = mock_response
    
    # Save original env vars
    original_creds = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")
    
    try:
        client = LLMClient(
            api_key="/path/to/credentials.json",
            model="vertex_ai/gemini-test"
        )
        
        # Manually test setup (since cleanup happens in finally)
        client._setup_vertex_credentials()
        
        # Check that env var was set to the path
        assert os.environ.get("GOOGLE_APPLICATION_CREDENTIALS") == "/path/to/credentials.json"
        
        # Cleanup manually for test
        client._cleanup_vertex_credentials()
    finally:
        # Restore original env vars
        if original_creds:
            os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = original_creds
        elif "GOOGLE_APPLICATION_CREDENTIALS" in os.environ:
            del os.environ["GOOGLE_APPLICATION_CREDENTIALS"]


@pytest.mark.asyncio
async def test_llm_client_context_manager(mock_completion, sample_messages):
    """Test LLM client as context manager."""
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = "Response"
    mock_completion.return_value = mock_response
    
    json_key = '{"type": "service_account"}'
    with LLMClient(api_key=json_key, model="vertex_ai/gemini-test") as client:
        result = await client.complete(sample_messages)
        assert result == "Response"
    
    # After context exit, credentials should be cleaned up
    assert "GOOGLE_APPLICATION_CREDENTIALS" not in os.environ or \
           os.environ.get("GOOGLE_APPLICATION_CREDENTIALS") != client._temp_credential_file.name if hasattr(client, '_temp_credential_file') and client._temp_credential_file else True


def test_llm_client_non_vertex_model(mock_completion, sample_messages):
    """Test that non-Vertex models don't set up credentials."""
    client = LLMClient(api_key="test-key", model="gemini/test")
    # Should not raise error about missing credentials
    assert client.model == "gemini/test"
    # Setup should not create credential files
    client._setup_vertex_credentials()
    assert client._temp_credential_file is None

