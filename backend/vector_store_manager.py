"""
Vector store initialization and management.
"""
import os
import logging
from typing import Optional

logger = logging.getLogger(__name__)

# Try to import vector store dependencies
try:
    from vector_store.faiss_store import FAISSVectorStore
    from vector_store.document_loader import prepare_documents_for_indexing
    from vector_store.index_utils import check_index_exists, ensure_index_directory
    VECTOR_STORE_AVAILABLE = True
except ImportError as e:
    import sys
    print(f"INFO: Vector store dependencies not available: {e}", file=sys.stdout)
    VECTOR_STORE_AVAILABLE = False
    FAISSVectorStore = None
    prepare_documents_for_indexing = None
    check_index_exists = None
    ensure_index_directory = None

import config


def initialize_vector_store():
    """Initialize vector store instance with lazy loading.
    
    Lazy-loads EmbeddingGenerator only when needed (for queries or building).
    Uses sentence-transformers for all embeddings (no Google API).
    """
    if not VECTOR_STORE_AVAILABLE:
        return None
    
    index_exists, index_path, _ = check_index_exists()
    
    if index_exists:
        logger.info(f"Index found at {index_path}")
    else:
        logger.info(f"Index not found at {index_path} - will attempt to build")
    
    # Lazy import EmbeddingGenerator - always needed (for queries if index exists, or building if missing)
    try:
        from vector_store.embeddings import EmbeddingGenerator
        embedding_gen = EmbeddingGenerator()
        if logger.isEnabledFor(logging.DEBUG):
            logger.debug("EmbeddingGenerator created successfully")
    except ImportError as e:
        error_msg = f"sentence-transformers not available: {e}"
        if index_exists:
            logger.warning(error_msg)
            logger.warning("Vector search requires sentence-transformers for query embeddings")
        else:
            logger.error(error_msg)
            logger.error("Cannot build index. Ensure sentence-transformers is installed (included in requirements.txt)")
        return None
    except Exception as e:
        error_msg = f"Error initializing embedding generator: {e}"
        logger.error(error_msg, exc_info=True)
        return None
    
    try:
        vector_store = FAISSVectorStore(embedding_gen, index_path=index_path)
        index_loaded = vector_store.index is not None and vector_store.index.ntotal > 0 if vector_store.index else False
        
        # Pre-warm embedding model with a dummy query to avoid first-query delay
        if index_loaded:
            if logger.isEnabledFor(logging.DEBUG):
                logger.debug("Pre-warming embedding model...")
            try:
                embedding_gen.embed("warmup")
                if logger.isEnabledFor(logging.DEBUG):
                    logger.debug("Embedding model warmed up")
            except Exception as e:
                logger.warning(f"Failed to warm up model: {e}")
        
        return vector_store
    except Exception as e:
        error_msg = f"Error creating FAISSVectorStore: {e}"
        logger.error(error_msg, exc_info=True)
        return None


def load_or_build_index(vector_store: Optional[FAISSVectorStore]):
    """Build index if it doesn't exist.
    
    Always attempts to build if index is missing, regardless of docs availability.
    """
    if not vector_store or not VECTOR_STORE_AVAILABLE:
        return
    
    # Check if index is already loaded (was found and loaded by FAISSVectorStore.__init__)
    if vector_store.index is not None and vector_store.index.ntotal > 0:
        logger.info(f"Vector store ready: {vector_store.index.ntotal} vectors loaded")
        return
    
    # Index doesn't exist - always attempt to build it
    index_exists, index_path, _ = check_index_exists()
    if index_exists:
        # Index exists but wasn't loaded - this shouldn't happen, but handle gracefully
        logger.warning(f"Index files exist at {index_path} but failed to load")
        return
    
    logger.info("Index not found - attempting to build from documentation...")
    
    # Ensure data directory exists
    ensure_index_directory(index_path)
    
    # Use docs directory from config (set by Dockerfile if index needs to be built)
    docs_dir = config.NEXTFLOW_DOCS_DIR
    
    # If docs_dir is not set or empty, try default location
    if not docs_dir or not docs_dir.strip():
        # Default location where Dockerfile clones docs (only if index doesn't exist)
        if os.path.exists("/app/nextflow-docs"):
            docs_dir = "/app/nextflow-docs"
        else:
            # If index doesn't exist and docs don't exist, we can't build
            logger.error("Index not found and NEXTFLOW_DOCS_DIR not set")
            logger.error("Dockerfile should clone Nextflow docs when index doesn't exist")
            return
    
    # Check if docs directory exists
    if not os.path.exists(docs_dir):
        # Docs directory was set but doesn't exist - this shouldn't happen, but handle gracefully
        logger.error(f"Docs directory not found: {docs_dir}")
        logger.error("If index doesn't exist, ensure Dockerfile clones Nextflow docs")
        return
    
    # Build index from documentation
    logger.info(f"Loading documents from: {docs_dir}")
    try:
        texts, metadata = prepare_documents_for_indexing(docs_dir=docs_dir)
        if texts and len(texts) > 0:
            logger.info(f"Building index from {len(texts)} document chunks...")
            vector_store.build_index(texts, metadata)
            logger.info(f"Vector store built successfully: {len(texts)} chunks indexed")
        else:
            logger.warning("No documents loaded from docs directory")
            logger.error("Unable to build vector index - no documents found")
    except Exception as e:
        logger.error(f"Failed to build index: {e}", exc_info=True)

