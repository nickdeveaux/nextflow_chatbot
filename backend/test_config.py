"""
Tests for configuration module.
Run with: pytest test_config.py -v
"""
import pytest
import os
import yaml
from pathlib import Path
import config


def test_google_vertex_api_key():
    """Test API key is defined."""
    assert config.GOOGLE_VERTEX_API_KEY is not None
    assert isinstance(config.GOOGLE_VERTEX_API_KEY, str)
    assert len(config.GOOGLE_VERTEX_API_KEY) > 0


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
    """Test docs directory is defined."""
    assert config.NEXTFLOW_DOCS_DIR is not None
    assert isinstance(config.NEXTFLOW_DOCS_DIR, str)


def test_vector_index_path():
    """Test vector index path is defined."""
    assert config.VECTOR_INDEX_PATH is not None
    assert isinstance(config.VECTOR_INDEX_PATH, str)


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


def test_default_citations():
    """Test default citations are defined."""
    assert config.DEFAULT_CITATIONS is not None
    assert isinstance(config.DEFAULT_CITATIONS, list)
    assert len(config.DEFAULT_CITATIONS) > 0
    for citation in config.DEFAULT_CITATIONS:
        assert isinstance(citation, str)
        assert citation.startswith("http")


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
    assert 'default_citations' in yaml_config


def test_env_var_override():
    """Test that environment variables can override YAML defaults."""
    original_value = config.LLM_TEMPERATURE
    os.environ["LLM_TEMPERATURE"] = "0.9"
    
    # Reload config to pick up env var
    import importlib
    importlib.reload(config)
    
    assert config.LLM_TEMPERATURE == 0.9
    
    # Restore
    del os.environ["LLM_TEMPERATURE"]
    importlib.reload(config)

