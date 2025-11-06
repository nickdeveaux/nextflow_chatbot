"""
LLM client for calling Gemini via Vertex AI using google-genai SDK.
"""
import os
import tempfile
from typing import List, Dict, Optional
from google import genai
import config
from google.genai import types
import google.auth
from google.oauth2 import service_account

class LLMClient:
    """Client for calling LLMs via Vertex AI using google-genai SDK."""
    
    def __init__(
        self,
        model: Optional[str] = None,
        project_id: Optional[str] = None,
        location: Optional[str] = None,
        max_tokens: Optional[int] = None,
        api_key: Optional[str] = None
    ):
        """
        Initialize LLM client.
        
        Args:
            model: Model name (defaults to config.LLM_MODEL)
            project_id: Google Cloud project ID (defaults to config.GOOGLE_CLOUD_PROJECT)
            location: Vertex AI location (defaults to 'us-central1')
            max_tokens: Max tokens (defaults to config.LLM_MAX_TOKENS)
            api_key: Service account JSON key or file path (defaults to config.GOOGLE_VERTEX_API_KEY)
        """
        self.model = model or config.LLM_MODEL
        self.project_id = project_id or config.GOOGLE_CLOUD_PROJECT
        self.location = location or "us-central1"
        self.max_tokens = max_tokens or config.LLM_MAX_TOKENS
        api_key_config = api_key or config.GOOGLE_VERTEX_API_KEY
        # Resolve relative paths relative to project root
        if api_key_config and not api_key_config.startswith("{") and not os.path.isabs(api_key_config):
            # If it's a relative path, resolve it relative to the project root (parent of backend)
            project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            api_key_config = os.path.join(project_root, api_key_config)
        self.api_key = api_key_config
        self._temp_credential_file = None
        
        if not self.project_id:
            raise ValueError("GOOGLE_CLOUD_PROJECT not set for Vertex AI")
        
        # Setup credentials
        credentials = self._get_credentials()
        
        # Initialize client with explicit credentials
        self.client = genai.Client(
            vertexai=True,
            project=self.project_id,
            location=self.location,
            credentials=credentials
        )
    
    def _get_credentials(self):
        """Get Google Cloud credentials from API key or ADC."""
        # If no API key provided, use Application Default Credentials
        if not self.api_key:
            try:
                credentials, _ = google.auth.default()
                return credentials
            except google.auth.exceptions.DefaultCredentialsError:
                raise ValueError(
                    "No credentials found. Set GOOGLE_APPLICATION_CREDENTIALS env var, "
                    "run 'gcloud auth application-default login', or provide a service account JSON key."
                )
        
        # Check if API key is JSON (service account key)
        api_key_stripped = self.api_key.strip()
        if api_key_stripped.startswith("{"):
            # Write JSON to temp file
            self._temp_credential_file = tempfile.NamedTemporaryFile(
                mode='w',
                suffix='.json',
                delete=False
            )
            self._temp_credential_file.write(self.api_key)
            self._temp_credential_file.close()
            creds_path = self._temp_credential_file.name
        elif os.path.exists(self.api_key) and os.path.isfile(self.api_key):
            # It's a valid file path to credentials
            creds_path = self.api_key
        else:
            # API key token - not supported for Vertex AI
            # Try to use ADC instead
            print(
                f"Warning: API key format not recognized for Vertex AI. "
                f"Attempting to use Application Default Credentials."
            )
            try:
                credentials, _ = google.auth.default()
                return credentials
            except google.auth.exceptions.DefaultCredentialsError:
                raise ValueError(
                    "Invalid API key format. Vertex AI requires a service account JSON key or file path. "
                    "Alternatively, set up Application Default Credentials via 'gcloud auth application-default login'."
                )
        
        # Load service account credentials
        try:
            credentials = service_account.Credentials.from_service_account_file(
                creds_path,
                scopes=['https://www.googleapis.com/auth/cloud-platform']
            )
            return credentials
        except Exception as e:
            raise ValueError(f"Failed to load credentials from {creds_path}: {e}")
    
    def __del__(self):
        """Cleanup temp credential file on deletion."""
        if self._temp_credential_file and os.path.exists(self._temp_credential_file.name):
            try:
                os.remove(self._temp_credential_file.name)
            except:
                pass
    
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
        
        contents = []
        
        # Add conversation messages as Content objects
        for msg in messages:
            role = msg.get("role", "user")
            content_text = msg.get("content", "")
            
            # Skip system role if system_prompt is provided (handled in config)
            if role == "system" and system_prompt:
                continue
            
            # Create Content object with Part
            content = types.Content(
                role=role,
                parts=[types.Part(text=content_text)]
            )
            contents.append(content)
        
        # Generate content
        # Use config parameter for generation settings
        # System instruction goes in config, not contents
        gen_config_params = {
            "max_output_tokens": self.max_tokens
        }
        
        if system_prompt:
            system_instruction = types.Content(
                role="system",
                parts=[types.Part(text=system_prompt)]
            )
            gen_config_params["system_instruction"] = system_instruction
        
        gen_config = types.GenerateContentConfig(**gen_config_params)
        
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
