"""
LLM client for calling Gemini via LiteLLM.
Supports both Vertex AI and Gemini public API endpoints.
"""
import os
import tempfile
from typing import List, Dict, Optional
from litellm import completion
import config


class LLMClient:
    """Client for calling LLMs via LiteLLM."""
    
    def __init__(
        self,
        model: Optional[str] = None,
        api_key: Optional[str] = None,
        project_id: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None
    ):
        """
        Initialize LLM client.
        
        Args:
            model: Model name (defaults to config.LLM_MODEL)
            api_key: API key (defaults to config.GOOGLE_VERTEX_API_KEY)
            project_id: Google Cloud project ID (defaults to config.GOOGLE_CLOUD_PROJECT)
            temperature: Temperature setting (defaults to config.LLM_TEMPERATURE)
            max_tokens: Max tokens (defaults to config.LLM_MAX_TOKENS)
        """
        self.model = model or config.LLM_MODEL
        self.api_key = api_key or config.GOOGLE_VERTEX_API_KEY
        self.project_id = project_id or config.GOOGLE_CLOUD_PROJECT
        self.temperature = temperature if temperature is not None else config.LLM_TEMPERATURE
        self.max_tokens = max_tokens or config.LLM_MAX_TOKENS
        self._temp_credential_file = None
    
    def _setup_vertex_credentials(self):
        """Setup Vertex AI credentials from API key."""
        if not self.model.startswith("vertex_ai/"):
            return
        
        if not self.api_key:
            raise ValueError("GOOGLE_VERTEX_API_KEY not set for Vertex AI model")
        
        # Check if API key is JSON (service account key)
        if self.api_key.strip().startswith("{"):
            # Write JSON to temp file
            self._temp_credential_file = tempfile.NamedTemporaryFile(
                mode='w',
                suffix='.json',
                delete=False
            )
            self._temp_credential_file.write(self.api_key)
            self._temp_credential_file.close()
            os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = self._temp_credential_file.name
        else:
            # Assume it's a path to credentials file
            os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = self.api_key
        
        # Set project ID if provided
        if self.project_id:
            os.environ["GOOGLE_CLOUD_PROJECT"] = self.project_id
    
    def _cleanup_vertex_credentials(self):
        """Clean up temporary credential files."""
        if self._temp_credential_file and os.path.exists(self._temp_credential_file.name):
            os.remove(self._temp_credential_file.name)
            self._temp_credential_file = None
        
        # Remove env vars if we set them
        if self.model.startswith("vertex_ai/"):
            os.environ.pop("GOOGLE_APPLICATION_CREDENTIALS", None)
            if self.project_id:
                os.environ.pop("GOOGLE_CLOUD_PROJECT", None)
    
    async def complete(
        self,
        messages: List[Dict[str, str]],
        system_prompt: Optional[str] = None
    ) -> str:
        """
        Complete a conversation with the LLM.
        
        Args:
            messages: List of message dicts with 'role' and 'content'
            system_prompt: Optional system prompt to prepend
        
        Returns:
            Response content string
        
        Raises:
            ValueError: If API key not set or response is empty
        """
        if not self.api_key:
            raise ValueError("API key not set")
        
        # Prepare messages with system prompt
        prepared_messages = messages.copy()
        if system_prompt:
            if not prepared_messages or prepared_messages[0].get("role") != "system":
                prepared_messages.insert(0, {"role": "system", "content": system_prompt})
        
        # Setup Vertex credentials if needed
        self._setup_vertex_credentials()
        
        try:
            # Prepare completion parameters
            completion_params = {
                "model": self.model,
                "messages": prepared_messages,
                "temperature": self.temperature,
                "max_tokens": self.max_tokens,
            }
            
            # For non-Vertex models, pass API key directly
            if not self.model.startswith("vertex_ai/"):
                completion_params["api_key"] = self.api_key
            
            response = completion(**completion_params)
            
            if not response or not response.choices:
                raise ValueError("Empty response from LLM")
            
            content = response.choices[0].message.content
            if not content:
                raise ValueError("Empty content in LLM response")
            
            return content
        finally:
            self._cleanup_vertex_credentials()
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - cleanup credentials."""
        self._cleanup_vertex_credentials()
        return False

