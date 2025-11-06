"""
Tests for LLM client using google-genai SDK.
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from llm_client import LLMClient
import config


@pytest.fixture
def mock_genai_client():
    """Mock google-genai Client."""
    with patch('llm_client.genai.Client') as mock:
        yield mock


@pytest.fixture
def sample_messages():
    """Sample messages for testing."""
    return [
        {"role": "user", "content": "What is Nextflow?"}
    ]


def test_llm_client_initialization():
    """Test LLM client initialization with defaults."""
    with patch('llm_client.genai.Client') as mock_client, \
         patch('llm_client.google.auth.default') as mock_auth:
        # Mock credentials
        mock_creds = MagicMock()
        mock_auth.return_value = (mock_creds, None)
        
        client = LLMClient()
        assert client.model == config.LLM_MODEL
        assert client.project_id == config.GOOGLE_CLOUD_PROJECT
        assert client.max_tokens == config.LLM_MAX_TOKENS
        # Check that credentials were passed
        call_kwargs = mock_client.call_args[1]
        assert call_kwargs["vertexai"] is True
        assert call_kwargs["project"] == config.GOOGLE_CLOUD_PROJECT
        assert call_kwargs["location"] == "us-central1"
        assert "credentials" in call_kwargs


def test_llm_client_custom_params():
    """Test LLM client with custom parameters."""
    with patch('llm_client.genai.Client') as mock_client, \
         patch('llm_client.google.auth.default') as mock_auth:
        # Mock credentials
        mock_creds = MagicMock()
        mock_auth.return_value = (mock_creds, None)
        
        client = LLMClient(
            model="test-model",
            project_id="test-project",
            location="us-west1",
            max_tokens=100
        )
        assert client.model == "test-model"
        assert client.project_id == "test-project"
        assert client.location == "us-west1"
        assert client.max_tokens == 100
        # Check that credentials were passed
        call_kwargs = mock_client.call_args[1]
        assert call_kwargs["vertexai"] is True
        assert call_kwargs["project"] == "test-project"
        assert call_kwargs["location"] == "us-west1"
        assert "credentials" in call_kwargs


def test_llm_client_no_project_id():
    """Test error when project ID is not set."""
    with patch('llm_client.genai.Client'):
        client = LLMClient()
        # Override to ensure it's None
        original_project = config.GOOGLE_CLOUD_PROJECT
        try:
            # Temporarily set config to None for this test
            import llm_client
            llm_client.config.GOOGLE_CLOUD_PROJECT = None
            client.project_id = None
            with pytest.raises(ValueError, match="GOOGLE_CLOUD_PROJECT not set"):
                LLMClient(project_id=None)
        finally:
            llm_client.config.GOOGLE_CLOUD_PROJECT = original_project


def test_llm_client_complete_success(mock_genai_client, sample_messages):
    """Test successful LLM completion."""
    # Mock response
    mock_response = MagicMock()
    mock_response.text = "Nextflow is a workflow system."
    
    mock_models = MagicMock()
    mock_models.generate_content.return_value = mock_response
    
    mock_client_instance = MagicMock()
    mock_client_instance.models = mock_models
    mock_genai_client.return_value = mock_client_instance
    
    client = LLMClient(project_id="test-project")
    result = client.complete(sample_messages)
    
    assert result == "Nextflow is a workflow system."
    mock_models.generate_content.assert_called_once()
    call_kwargs = mock_models.generate_content.call_args[1]
    assert call_kwargs["model"] == config.LLM_MODEL
    # Check config object has max_output_tokens
    assert call_kwargs["config"].max_output_tokens == config.LLM_MAX_TOKENS


def test_llm_client_with_system_prompt(mock_genai_client, sample_messages):
    """Test LLM client with system prompt."""
    mock_response = MagicMock()
    mock_response.text = "Response"
    
    mock_models = MagicMock()
    mock_models.generate_content.return_value = mock_response
    
    mock_client_instance = MagicMock()
    mock_client_instance.models = mock_models
    mock_genai_client.return_value = mock_client_instance
    
    client = LLMClient(project_id="test-project")
    result = client.complete(sample_messages, system_prompt="You are a helpful assistant.")
    
    assert result == "Response"
    # Check that system prompt was passed in config.system_instruction
    call_args = mock_models.generate_content.call_args
    call_kwargs = call_args[1]
    # System instruction should be in config
    config = call_kwargs["config"]
    assert config.system_instruction is not None
    assert config.system_instruction.role == "system"
    assert config.system_instruction.parts[0].text == "You are a helpful assistant."
    # User message should be in contents
    contents = call_kwargs["contents"]
    assert len(contents) == 1
    assert contents[0].role == "user"
    assert contents[0].parts[0].text == sample_messages[0]["content"]


def test_llm_client_empty_response(mock_genai_client, sample_messages):
    """Test handling of empty LLM response."""
    mock_response = MagicMock()
    mock_response.text = None
    
    mock_models = MagicMock()
    mock_models.generate_content.return_value = mock_response
    
    mock_client_instance = MagicMock()
    mock_client_instance.models = mock_models
    mock_genai_client.return_value = mock_client_instance
    
    client = LLMClient(project_id="test-project")
    with pytest.raises(ValueError, match="Empty response from LLM"):
        client.complete(sample_messages)


def test_llm_client_context_manager(mock_genai_client, sample_messages):
    """Test LLM client as context manager."""
    mock_response = MagicMock()
    mock_response.text = "Response"
    
    mock_models = MagicMock()
    mock_models.generate_content.return_value = mock_response
    
    mock_client_instance = MagicMock()
    mock_client_instance.models = mock_models
    mock_genai_client.return_value = mock_client_instance
    
    with LLMClient(project_id="test-project") as client:
        result = client.complete(sample_messages)
        assert result == "Response"


def test_llm_client_multi_turn_conversation(mock_genai_client):
    """Test multi-turn conversation handling."""
    mock_response = MagicMock()
    mock_response.text = "Follow-up response"
    
    mock_models = MagicMock()
    mock_models.generate_content.return_value = mock_response
    
    mock_client_instance = MagicMock()
    mock_client_instance.models = mock_models
    mock_genai_client.return_value = mock_client_instance
    
    client = LLMClient(project_id="test-project")
    messages = [
        {"role": "user", "content": "What is Nextflow?"},
        {"role": "assistant", "content": "Nextflow is a workflow system."},
        {"role": "user", "content": "Tell me more."}
    ]
    
    result = client.complete(messages)
    assert result == "Follow-up response"
    
    # Verify all messages were passed
    call_args = mock_models.generate_content.call_args
    contents = call_args[1]["contents"]
    assert len(contents) == 3
    assert contents[0].role == "user"
    assert contents[1].role == "assistant"
    assert contents[2].role == "user"
