"""
Pydantic models for API requests and responses.
"""
from pydantic import BaseModel
from typing import List, Optional


class ChatMessage(BaseModel):
    """Chat message request model."""
    message: str
    session_id: Optional[str] = None


class ChatResponse(BaseModel):
    """Chat response model."""
    reply: str
    session_id: str
    citations: Optional[List[str]] = None

