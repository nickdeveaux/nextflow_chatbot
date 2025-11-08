"""
Session management for chat conversations.
"""
from typing import Dict, List
from datetime import datetime
import uuid
import logging

logger = logging.getLogger(__name__)

# In-memory session storage
sessions: Dict[str, List[Dict]] = {}


def get_or_create_session(session_id: str = None) -> str:
    """Get existing session or create new one."""
    if not session_id:
        session_id = str(uuid.uuid4())
    
    # Ensure session exists in dict
    if session_id not in sessions:
        sessions[session_id] = []
    
    return session_id


def add_user_message(session_id: str, message: str):
    """Add user message to session."""
    sessions[session_id].append({
        "role": "user",
        "content": message,
        "timestamp": datetime.now().isoformat()
    })


def add_assistant_message(session_id: str, reply: str):
    """Add assistant message to session."""
    sessions[session_id].append({
        "role": "assistant",
        "content": reply,
        "timestamp": datetime.now().isoformat()
    })


def get_conversation_history(session_id: str) -> List[Dict]:
    """Get conversation history for a session."""
    return sessions.get(session_id, []).copy()


def clear_session(session_id: str):
    """Clear a session (for testing)."""
    if session_id in sessions:
        del sessions[session_id]

