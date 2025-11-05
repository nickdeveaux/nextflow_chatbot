"""
Embedding generation for vector store.
Supports both OpenAI embeddings and sentence-transformers.
"""
import os
from typing import List, Optional
import numpy as np

try:
    from sentence_transformers import SentenceTransformer
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    SENTENCE_TRANSFORMERS_AVAILABLE = False

try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False


class EmbeddingGenerator:
    """Generate embeddings for text using various backends."""
    
    def __init__(self, use_openai: bool = False):
        """
        Initialize embedding generator.
        
        Args:
            use_openai: If True, use OpenAI embeddings. Otherwise use sentence-transformers.
        """
        self.use_openai = use_openai and OPENAI_AVAILABLE
        self.model = None
        self.openai_client = None
        
        if self.use_openai:
            api_key = os.getenv("OPENAI_API_KEY")
            if api_key:
                self.openai_client = openai.OpenAI(api_key=api_key)
            else:
                print("Warning: OPENAI_API_KEY not set, falling back to sentence-transformers")
                self.use_openai = False
        
        if not self.use_openai:
            if not SENTENCE_TRANSFORMERS_AVAILABLE:
                raise ImportError(
                    "Neither OpenAI nor sentence-transformers available. "
                    "Install with: pip install sentence-transformers"
                )
            # Use a lightweight model for fast embeddings
            self.model = SentenceTransformer('all-MiniLM-L6-v2')
    
    def embed(self, text: str) -> np.ndarray:
        """Generate embedding for a single text."""
        if self.use_openai and self.openai_client:
            response = self.openai_client.embeddings.create(
                model="text-embedding-3-small",
                input=text
            )
            return np.array(response.data[0].embedding)
        else:
            return self.model.encode(text, convert_to_numpy=True)
    
    def embed_batch(self, texts: List[str]) -> np.ndarray:
        """Generate embeddings for multiple texts."""
        if self.use_openai and self.openai_client:
            response = self.openai_client.embeddings.create(
                model="text-embedding-3-small",
                input=texts
            )
            return np.array([item.embedding for item in response.data])
        else:
            return self.model.encode(texts, convert_to_numpy=True)
    
    @property
    def dimension(self) -> int:
        """Get the dimension of embeddings."""
        if self.use_openai:
            return 1536  # text-embedding-3-small dimension
        else:
            return 384  # all-MiniLM-L6-v2 dimension

