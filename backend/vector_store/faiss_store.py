"""
FAISS-based vector store for semantic search.
"""
import numpy as np
import faiss
import pickle
import os
from typing import List, Tuple, Optional

from .embeddings import EmbeddingGenerator


class FAISSVectorStore:
    """FAISS-based vector store with cosine similarity search."""
    
    def __init__(self, embedding_generator: EmbeddingGenerator, index_path: Optional[str] = None):
        """
        Initialize vector store.
        
        Args:
            embedding_generator: EmbeddingGenerator instance
            index_path: Path to save/load FAISS index (optional)
        """
        self.embedding_generator = embedding_generator
        self.index_path = index_path
        self.index = None
        self.documents = []  # Store original text chunks
        self.metadata = []   # Store metadata (source, url, etc.)
        self.dimension = embedding_generator.dimension
        
        # Load existing index if available
        if index_path and os.path.exists(index_path):
            self.load(index_path)
    
    def build_index(self, documents: List[str], metadata: Optional[List[dict]] = None):
        """
        Build FAISS index from documents.
        
        Args:
            documents: List of text chunks to index
            metadata: Optional list of metadata dicts for each document
        """
        print(f"Building FAISS index for {len(documents)} documents...")
        
        # Generate embeddings
        embeddings = self.embedding_generator.embed_batch(documents)
        
        # Normalize embeddings for cosine similarity (L2 normalization)
        faiss.normalize_L2(embeddings)
        
        # Create FAISS index (Inner Product = cosine similarity for normalized vectors)
        self.index = faiss.IndexFlatIP(self.dimension)
        
        # Add embeddings to index
        self.index.add(embeddings.astype('float32'))
        
        # Store documents and metadata
        self.documents = documents
        # Ensure metadata list matches documents length
        if metadata is None:
            self.metadata = [{}] * len(documents)
        else:
            # Pad metadata if shorter than documents
            if len(metadata) < len(documents):
                self.metadata = metadata + [{}] * (len(documents) - len(metadata))
            else:
                self.metadata = metadata[:len(documents)]
        
        print(f"Index built with {self.index.ntotal} vectors")
        
        # Save if path provided
        if self.index_path:
            self.save(self.index_path)
    
    def search(self, query: str, top_k: int = 3, threshold: float = 0.0) -> List[Tuple[str, float, dict]]:
        """
        Search for similar documents using cosine similarity.
        
        Args:
            query: Query text
            top_k: Number of results to return
            threshold: Minimum similarity threshold (0.0 to 1.0)
        
        Returns:
            List of (document_text, similarity_score, metadata) tuples
        """
        if self.index is None or self.index.ntotal == 0:
            return []
        
        # Generate query embedding
        query_embedding = self.embedding_generator.embed(query)
        
        # Normalize for cosine similarity
        # Reshape to 2D array (1 query, dimension features) for FAISS
        query_embedding = query_embedding.astype('float32').reshape(1, -1)
        faiss.normalize_L2(query_embedding)
        
        # Search (query_embedding is now 2D: [1, dimension])
        similarities, indices = self.index.search(query_embedding, min(top_k, self.index.ntotal))
        
        # Filter by threshold and format results
        results = []
        similarity_array = similarities[0] if len(similarities.shape) > 1 else similarities
        indices_array = indices[0] if len(indices.shape) > 1 else indices
        
        for similarity, idx in zip(similarity_array, indices_array):
            if idx >= 0 and similarity >= threshold:
                # Ensure idx is within bounds
                if idx >= len(self.documents):
                    continue
                
                # Get metadata safely
                if idx < len(self.metadata):
                    metadata = self.metadata[idx]
                else:
                    metadata = {}
                
                # Ensure metadata is a dict
                if not isinstance(metadata, dict):
                    metadata = {}
                
                results.append((
                    self.documents[idx],
                    float(similarity),
                    metadata
                ))
        
        return results
    
    def save(self, path: str):
        """Save index and documents to disk."""
        print(f"Saving index to {path}...")
        os.makedirs(os.path.dirname(path) if os.path.dirname(path) else '.', exist_ok=True)
        
        # Save FAISS index
        faiss.write_index(self.index, path)
        
        # Save documents and metadata
        data_path = path.replace('.index', '.data')
        with open(data_path, 'wb') as f:
            pickle.dump({
                'documents': self.documents,
                'metadata': self.metadata,
                'dimension': self.dimension
            }, f)
        
        print("Index saved successfully")
    
    def load(self, path: str):
        """Load index and documents from disk."""
        print(f"Loading index from {path}...")
        
        if not os.path.exists(path):
            print(f"Index file not found: {path}")
            return
        
        # Load FAISS index
        self.index = faiss.read_index(path)
        
        # Get actual dimension from loaded index
        index_dimension = self.index.d if hasattr(self.index, 'd') else self.dimension
        
        # Load documents and metadata
        data_path = path.replace('.index', '.data')
        if os.path.exists(data_path):
            with open(data_path, 'rb') as f:
                data = pickle.load(f)
                self.documents = data.get('documents', [])
                self.metadata = data.get('metadata', [])
                # Use dimension from data file, or from index, or fallback to embedding generator
                stored_dimension = data.get('dimension', index_dimension)
                self.dimension = stored_dimension if stored_dimension else self.dimension
                
                # Warn if dimension mismatch
                if self.embedding_generator.dimension != self.dimension:
                    print(f"WARNING: Index dimension ({self.dimension}) doesn't match embedding generator dimension ({self.embedding_generator.dimension})")
                    print(f"This may cause search failures. Rebuild index with matching embedding model.")
                
                # Ensure metadata matches documents length
                if len(self.metadata) < len(self.documents):
                    self.metadata.extend([{}] * (len(self.documents) - len(self.metadata)))
                elif len(self.metadata) > len(self.documents):
                    self.metadata = self.metadata[:len(self.documents)]
        else:
            # If data file doesn't exist, initialize empty
            self.documents = []
            self.metadata = []
            # Use dimension from index
            self.dimension = index_dimension if index_dimension else self.dimension
        
        print(f"Index loaded with {self.index.ntotal} vectors (dimension: {self.dimension})")
    
    def add_documents(self, documents: List[str], metadata: Optional[List[dict]] = None):
        """Add new documents to existing index."""
        if self.index is None:
            self.build_index(documents, metadata)
            return
        
        # Generate embeddings for new documents
        embeddings = self.embedding_generator.embed_batch(documents)
        faiss.normalize_L2(embeddings)
        
        # Add to index
        self.index.add(embeddings.astype('float32'))
        
        # Update documents and metadata
        self.documents.extend(documents)
        if metadata:
            self.metadata.extend(metadata)
        else:
            self.metadata.extend([{}] * len(documents))
        
        # Save if path provided
        if self.index_path:
            self.save(self.index_path)

