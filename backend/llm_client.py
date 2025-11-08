"""
LLM client for calling Gemini via Vertex AI using google-genai SDK.
"""
import os
import logging
from typing import List, Dict, Optional
from google import genai
import config
from google.genai import types
from google.oauth2 import service_account

logger = logging.getLogger(__name__)


class LLMClient:
    """Client for calling LLMs via Vertex AI using google-genai SDK."""
    
    def __init__(
        self,
        model: Optional[str] = None,
        location: Optional[str] = None,
        max_tokens: Optional[int] = None,
        service_account_path: Optional[str] = None
    ):
        """
        Initialize LLM client.
        
        Args:
            model: Model name (defaults to config.LLM_MODEL)
            project_id: Google Cloud project ID (defaults to config.GOOGLE_CLOUD_PROJECT)
            location: Vertex AI location (defaults to 'us-central1')
            max_tokens: Max tokens (defaults to config.LLM_MAX_TOKENS)
            service_account_path: Path to service account JSON file (defaults to config.SERVICE_ACCOUNT_PATH)
        """
        self.model = model or config.LLM_MODEL
        self.location = location or "us-central1"
        self.max_tokens = max_tokens or config.LLM_MAX_TOKENS

        credentials = service_account.Credentials.from_service_account_file(
            os.environ["GOOGLE_APPLICATION_CREDENTIALS"],
            scopes=['https://www.googleapis.com/auth/cloud-platform']
        )
        if not credentials:
            raise ValueError("GOOGLE_APPLICATION_CREDENTIALS missing in LLMClient!")
        self.project_id = credentials.project_id
        if not self.project_id:
            raise ValueError("GOOGLE_CLOUD_PROJECT not set for Vertex AI in LLMClient!")
    
        # Initialize client
        self.client = genai.Client(
            vertexai=True,
            project=self.project_id,
            location=self.location,
            credentials=credentials
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
        
        logger.info(f"Sending to LLM (model={self.model}):")
        resp = self.client.models.generate_content(
            model=self.model,
            contents=contents,
            config=gen_config
        )
        
        if not resp.text:
            raise ValueError("Empty response from LLM")
        
        return resp.text
