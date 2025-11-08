"""
LLM utility functions for building messages and system prompts.
"""
from typing import List, Dict
import config


def get_system_prompt() -> str:
    """Get Nextflow-specific system prompt."""
    base_prompt = config.SYSTEM_PROMPT
    
    # Add max_output_tokens information to prompt
    max_tokens_info = f"\n\nIMPORTANT: Keep responses concise. You have a maximum output limit of {config.LLM_MAX_TOKENS} tokens. Be terse and focused in your responses."
    
    return f"{base_prompt}{max_tokens_info}"


def build_messages(conversation_history: List[Dict], query: str, context: str = "") -> List[Dict]:
    """Build message list for LLM."""
    messages = []
    if conversation_history:
        for msg in conversation_history:
            messages.append({"role": msg["role"], "content": msg["content"]})
    
    user_message = query
    if context:
        user_message = f"Context from documentation:\n{context}\n\nUser question: {query}"
    
    messages.append({"role": "user", "content": user_message})
    return messages

