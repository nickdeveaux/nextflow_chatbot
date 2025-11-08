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
    print("INFO: Running in LLM-only mode (no vector search)", file=sys.stdout)
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
        if logger.isEnabledFor(logging.DEBUG):
            logger.debug("Vector store dependencies not available - running in LLM-only mode")
        return None
    
    index_exists, index_path, _ = check_index_exists()
    
    if index_exists:
        logger.info(f"Index found at {index_path}")
    else:
        logger.info(f"Index not found at {index_path}")
        if logger.isEnabledFor(logging.DEBUG):
            logger.debug("  Index will be built if NEXTFLOW_DOCS_DIR is available")
    
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
    
    Note: If index exists, it's already loaded by FAISSVectorStore.__init__.
    This function only handles building a new index from documentation.
    """
    if not vector_store or not VECTOR_STORE_AVAILABLE:
        logger.info("Vector store not available - running in LLM-only mode")
        return
    
    # Check if index is already loaded (was found and loaded by FAISSVectorStore.__init__)
    if vector_store.index is not None and vector_store.index.ntotal > 0:
        logger.info(f"Vector store ready: {vector_store.index.ntotal} vectors loaded")
        return
    
    # Index doesn't exist - try to build it
    index_exists, index_path, _ = check_index_exists()
    if index_exists:
        # Index exists but wasn't loaded - this shouldn't happen, but handle gracefully
        logger.warning(f"Index files exist at {index_path} but failed to load")
        return
    
    if logger.isEnabledFor(logging.DEBUG):
        logger.debug("Index not found - attempting to build from documentation...")
    
    # Ensure data directory exists
    ensure_index_directory(index_path)
    
    # Check if docs directory is available
    if not config.NEXTFLOW_DOCS_DIR or not os.path.exists(config.NEXTFLOW_DOCS_DIR):
        logger.info("NEXTFLOW_DOCS_DIR not set or docs not found - running in LLM-only mode")
        if logger.isEnabledFor(logging.DEBUG):
            logger.debug(f"  NEXTFLOW_DOCS_DIR: {config.NEXTFLOW_DOCS_DIR}")
            logger.debug("  To enable vector search: Set NEXTFLOW_DOCS_DIR or commit pre-built index files")
        return
    
    # Build index from documentation
    if logger.isEnabledFor(logging.DEBUG):
        logger.debug(f"Loading documents from: {config.NEXTFLOW_DOCS_DIR}")
    try:
        texts, metadata = prepare_documents_for_indexing(docs_dir=config.NEXTFLOW_DOCS_DIR)
        if texts:
            logger.info(f"Building index from {len(texts)} document chunks...")
            vector_store.build_index(texts, metadata)
            logger.info(f"Vector store built successfully: {len(texts)} chunks indexed")
        else:
            logger.warning("No documents loaded from docs directory - running in LLM-only mode")
    except Exception as e:
        logger.error(f"Error building vector store index: {e}", exc_info=True)
        logger.info("Failed to build index - running in LLM-only mode")

