"""
LLM client for calling Gemini via Vertex AI using google-genai SDK.
"""
import os
from typing import List, Dict, Optional
from google import genai
import config


class LLMClient:
    """Client for calling LLMs via Vertex AI using google-genai SDK."""
    
    def __init__(
        self,
        model: Optional[str] = None,
        project_id: Optional[str] = None,
        location: Optional[str] = None,
        max_tokens: Optional[int] = None
    ):
        """
        Initialize LLM client.
        
        Args:
            model: Model name (defaults to config.LLM_MODEL)
            project_id: Google Cloud project ID (defaults to config.GOOGLE_CLOUD_PROJECT)
            location: Vertex AI location (defaults to 'us-central1')
            max_tokens: Max tokens (defaults to config.LLM_MAX_TOKENS)
        """
        self.model = model or config.LLM_MODEL
        self.project_id = project_id or config.GOOGLE_CLOUD_PROJECT
        self.location = location or "us-central1"
        self.max_tokens = max_tokens or config.LLM_MAX_TOKENS
        
        if not self.project_id:
            raise ValueError("GOOGLE_CLOUD_PROJECT not set for Vertex AI")
        
        # Initialize client - uses Application Default Credentials
        # Set GOOGLE_APPLICATION_CREDENTIALS env var or use gcloud auth
        self.client = genai.Client(
            vertexai=True,
            project=self.project_id,
            location=self.location
        )
    
    def complete(
        self,
        messages: List[Dict[str, str]],
        system_prompt: Optional[str] = None
    ) -> str:
        """
        Complete a conversation with the LLM.
        
        Args:
            messages: List of message dicts with 'role' and 'content'
            system_prompt: Optional system prompt (passed as systemInstruction)
        
        Returns:
            Response content string
        
        Raises:
            ValueError: If response is empty
        """
        # Prepare contents for SDK
        contents = []
        
        # Add system prompt as systemInstruction if provided
        if system_prompt:
            contents.append({"role": "system", "text": system_prompt})
        
        # Add conversation messages
        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            
            # Skip system role if already handled via system_prompt
            if role == "system" and system_prompt:
                continue
            
            contents.append({"role": role, "text": content})
        
        # Generate content
        # Use config parameter for generation settings
        from google.genai import types
        gen_config = types.GenerateContentConfig(
            max_output_tokens=self.max_tokens
        )
        resp = self.client.models.generate_content(
            model=self.model,
            contents=contents,
            config=gen_config
        )
        
        if not resp.text:
            raise ValueError("Empty response from LLM")
        
        return resp.text
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        return False
