"""
Embedding generation for vector store.
Optimized for CPU speed and low memory use.
"""
from typing import List
import numpy as np
import os

# Disable all progress bars and logs globally
os.environ.setdefault("SENTENCE_TRANSFORMERS_HOME", "/tmp/.cache")
os.environ["TOKENIZERS_PARALLELISM"] = "false"
os.environ["TQDM_DISABLE"] = "1"
os.environ["TRANSFORMERS_VERBOSITY"] = "error"

# Suppress all logging from sentence-transformers and transformers
import logging
logging.getLogger("sentence_transformers").setLevel(logging.ERROR)
logging.getLogger("transformers").setLevel(logging.ERROR)
logging.getLogger("transformers.configuration_utils").setLevel(logging.ERROR)
logging.getLogger("transformers.tokenization_utils_base").setLevel(logging.ERROR)
logging.getLogger("transformers.modeling_utils").setLevel(logging.ERROR)
logging.getLogger("huggingface_hub").setLevel(logging.ERROR)

try:
    from sentence_transformers import SentenceTransformer
    import torch
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    SENTENCE_TRANSFORMERS_AVAILABLE = False


class EmbeddingGenerator:
    """Generate embeddings using sentence-transformers with CPU optimizations."""

    def __init__(self):
        if not SENTENCE_TRANSFORMERS_AVAILABLE:
            raise ImportError(
                "sentence-transformers not available. "
                "Install with: pip install sentence-transformers"
            )

        # Force single-threaded Torch for small CPU servers
        # Prevents CPU thread oversubscription (huge win on small Railway/Heroku boxes)
        torch.set_num_threads(int(os.environ.get("TORCH_NUM_THREADS", "1")))

        # Use lightweight model (384-dim) and lazy-load on CPU
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.model = SentenceTransformer(
            "sentence-transformers/all-MiniLM-L6-v2",
            device=self.device
        )
        # Disable automatic model evaluation warnings
        self.model.eval()

    def embed(self, text: str) -> np.ndarray:
        """Generate embedding for one text (CPU-optimized, silent)."""
        return self.model.encode(
            [text],
            convert_to_numpy=True,
            normalize_embeddings=False,
            show_progress_bar=False,
            batch_size=1
        )[0]

    def embed_batch(self, texts: List[str]) -> np.ndarray:
        """Generate embeddings for many texts (fast on CPU)."""
        return self.model.encode(
            texts,
            convert_to_numpy=True,
            normalize_embeddings=False,
            show_progress_bar=False,
            batch_size=64 if self.device == "cuda" else 16
        )

    @property
    def dimension(self) -> int:
        return 384
