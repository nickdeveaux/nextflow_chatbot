"""
Tests for configuration module.
Run with: pytest test_config.py -v
"""
import os
import yaml
from pathlib import Path
import config

def test_llm_model():
    """Test LLM model is defined."""
    assert config.LLM_MODEL is not None
    assert isinstance(config.LLM_MODEL, str)
    assert len(config.LLM_MODEL) > 0


def test_llm_temperature():
    """Test temperature is a valid float."""
    assert isinstance(config.LLM_TEMPERATURE, float)
    assert 0.0 <= config.LLM_TEMPERATURE <= 2.0


def test_llm_max_tokens():
    """Test max tokens is a valid integer."""
    assert isinstance(config.LLM_MAX_TOKENS, int)
    assert config.LLM_MAX_TOKENS > 0


def test_nextflow_docs_dir():
    """Test docs directory is defined (may be empty)."""
    assert config.NEXTFLOW_DOCS_DIR is not None
    assert isinstance(config.NEXTFLOW_DOCS_DIR, str)


def test_vector_index_path():
    """Test vector index path is defined."""
    assert config.VECTOR_INDEX_PATH is not None
    assert isinstance(config.VECTOR_INDEX_PATH, str)
    assert len(config.VECTOR_INDEX_PATH) > 0


def test_vector_search_config():
    """Test vector search configuration."""
    assert isinstance(config.VECTOR_SEARCH_TOP_K, int)
    assert config.VECTOR_SEARCH_TOP_K > 0
    assert isinstance(config.VECTOR_SEARCH_THRESHOLD, float)
    assert 0.0 <= config.VECTOR_SEARCH_THRESHOLD <= 1.0


def test_system_prompt():
    """Test system prompt is defined and contains key terms."""
    assert config.SYSTEM_PROMPT is not None
    assert isinstance(config.SYSTEM_PROMPT, str)
    assert len(config.SYSTEM_PROMPT) > 50
    assert "Nextflow" in config.SYSTEM_PROMPT
    assert "assistant" in config.SYSTEM_PROMPT.lower()


def test_config_yaml_exists():
    """Test that config.yaml exists and is valid."""
    config_path = Path(__file__).parent.parent / "config.yaml"
    assert config_path.exists(), "config.yaml should exist"
    
    with open(config_path, 'r') as f:
        yaml_config = yaml.safe_load(f)
    
    assert 'api' in yaml_config
    assert 'llm' in yaml_config
    assert 'system_prompt' in yaml_config
    assert 'vector_store' in yaml_config


def test_service_account_path():
    """Test service account path type (may be None if not configured)."""
    # SERVICE_ACCOUNT_PATH can be None if no service account is configured
    # (this is valid - the app just won't be able to use the LLM)
    # Or it can be a string path (even if file doesn't exist, that's handled by LLM client)
    assert config.SERVICE_ACCOUNT_PATH is None or isinstance(config.SERVICE_ACCOUNT_PATH, str)
    if config.SERVICE_ACCOUNT_PATH is not None:
        assert len(config.SERVICE_ACCOUNT_PATH) > 0

