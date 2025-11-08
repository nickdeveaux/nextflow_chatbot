"""
Security utilities for prompt injection detection.
"""
import logging

logger = logging.getLogger(__name__)


def check_prompt_injection(message: str) -> bool:
    """
    Light guardrail to detect potential prompt injection attempts.
    Returns True if suspicious patterns are detected.
    """
    message_lower = message.lower()
    
    # Common prompt injection patterns
    suspicious_patterns = [
        "ignore previous instructions",
        "forget your role",
        "you are now",
        "act as",
        "pretend to be",
        "new instructions:",
        "override",
        "new system prompt",
        "previous prompt",
        "original prompt",
    ]
    
    # Check for suspicious patterns
    for pattern in suspicious_patterns:
        if pattern in message_lower:
            logger.warning(f"Potential prompt injection detected: pattern '{pattern}' in message")
            return True
    
    # Check for excessive role-playing attempts (multiple role indicators)
    role_indicators = message_lower.count("you are") + message_lower.count("you're")
    if role_indicators > 2:
        logger.warning(f"Potential prompt injection: excessive role indicators ({role_indicators})")
        return True
    
    return False

