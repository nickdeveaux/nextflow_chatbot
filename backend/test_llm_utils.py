"""Unit tests for LLM utilities."""
import pytest
from llm_utils import get_system_prompt, build_messages
import config


def test_get_system_prompt():
    """Test that system prompt includes base prompt and max tokens info."""
    prompt = get_system_prompt()
    assert config.SYSTEM_PROMPT in prompt
    assert str(config.LLM_MAX_TOKENS) in prompt
    assert "IMPORTANT" in prompt
    assert "concise" in prompt.lower()


def test_build_messages_no_history():
    """Test building messages with no conversation history."""
    messages = build_messages([], "What is Nextflow?")
    assert len(messages) == 1
    assert messages[0]["role"] == "user"
    assert messages[0]["content"] == "What is Nextflow?"


def test_build_messages_with_history():
    """Test building messages with conversation history."""
    history = [
        {"role": "user", "content": "Hello"},
        {"role": "assistant", "content": "Hi!"},
    ]
    messages = build_messages(history, "What is Nextflow?")
    assert len(messages) == 3
    assert messages[0]["role"] == "user"
    assert messages[1]["role"] == "assistant"
    assert messages[2]["role"] == "user"
    assert messages[2]["content"] == "What is Nextflow?"


def test_build_messages_with_context():
    """Test building messages with context."""
    messages = build_messages([], "What is Nextflow?", "Nextflow is a workflow system.")
    assert len(messages) == 1
    assert "Context from documentation:" in messages[0]["content"]
    assert "Nextflow is a workflow system." in messages[0]["content"]
    assert "User question: What is Nextflow?" in messages[0]["content"]


def test_build_messages_with_history_and_context():
    """Test building messages with both history and context."""
    history = [{"role": "user", "content": "Hello"}]
    messages = build_messages(history, "What is Nextflow?", "Context here")
    assert len(messages) == 2
    assert messages[1]["content"] == "Context from documentation:\nContext here\n\nUser question: What is Nextflow?"

