"""Unit tests for session_manager."""
import pytest
from session_manager import (
    get_or_create_session, add_user_message, add_assistant_message,
    get_conversation_history, clear_session, sessions
)


def setup_function():
    """Clear sessions before each test."""
    sessions.clear()


def test_get_or_create_session_new():
    """Test creating a new session."""
    session_id = get_or_create_session()
    assert session_id is not None
    assert session_id in sessions
    assert sessions[session_id] == []


def test_get_or_create_session_existing():
    """Test getting an existing session."""
    session_id = get_or_create_session()
    session_id2 = get_or_create_session(session_id)
    assert session_id == session_id2
    assert len(sessions) == 1


def test_add_user_message():
    """Test adding a user message."""
    session_id = get_or_create_session()
    add_user_message(session_id, "Hello")
    
    history = get_conversation_history(session_id)
    assert len(history) == 1
    assert history[0]["role"] == "user"
    assert history[0]["content"] == "Hello"
    assert "timestamp" in history[0]


def test_add_assistant_message():
    """Test adding an assistant message."""
    session_id = get_or_create_session()
    add_assistant_message(session_id, "Hi there!")
    
    history = get_conversation_history(session_id)
    assert len(history) == 1
    assert history[0]["role"] == "assistant"
    assert history[0]["content"] == "Hi there!"
    assert "timestamp" in history[0]


def test_conversation_history():
    """Test getting conversation history."""
    session_id = get_or_create_session()
    add_user_message(session_id, "Hello")
    add_assistant_message(session_id, "Hi!")
    add_user_message(session_id, "How are you?")
    
    history = get_conversation_history(session_id)
    assert len(history) == 3
    assert history[0]["role"] == "user"
    assert history[1]["role"] == "assistant"
    assert history[2]["role"] == "user"


def test_clear_session():
    """Test clearing a session."""
    session_id = get_or_create_session()
    add_user_message(session_id, "Hello")
    assert len(sessions[session_id]) == 1
    
    clear_session(session_id)
    assert session_id not in sessions

