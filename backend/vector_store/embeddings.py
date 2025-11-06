"""
Embedding generation for vector store.
Uses sentence-transformers for embeddings.
"""
from typing import List
import numpy as np

try:
    from sentence_transformers import SentenceTransformer
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    SENTENCE_TRANSFORMERS_AVAILABLE = False


class EmbeddingGenerator:
    """Generate embeddings for text using sentence-transformers."""
    
    def __init__(self):
        """Initialize embedding generator."""
        if not SENTENCE_TRANSFORMERS_AVAILABLE:
            raise ImportError(
                "sentence-transformers not available. "
                "Install with: pip install sentence-transformers"
            )
        # Use a lightweight model for fast embeddings
        self.model = SentenceTransformer('all-MiniLM-L6-v2')
    
    def embed(self, text: str) -> np.ndarray:
        """Generate embedding for a single text."""
        return self.model.encode(text, convert_to_numpy=True)
    
    def embed_batch(self, texts: List[str]) -> np.ndarray:
        """Generate embeddings for multiple texts."""
        return self.model.encode(texts, convert_to_numpy=True)
    
    @property
    def dimension(self) -> int:
        """Get the dimension of embeddings."""
        return 384  # all-MiniLM-L6-v2 dimension

