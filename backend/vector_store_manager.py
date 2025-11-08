"""
Vector store initialization and management.
"""
import os
import logging
import subprocess
import shutil
import tempfile
from typing import Optional
from pathlib import Path

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


def clone_nextflow_docs(target_dir: str = None, branch: str = "master") -> Optional[str]:
    """Clone Nextflow documentation from GitHub.
    
    Args:
        target_dir: Directory to clone docs into. If None, uses /app/nextflow-docs or temp directory.
        branch: Git branch to clone (default: master)
    
    Returns:
        Path to docs directory if successful, None otherwise
    """
    if target_dir is None:
        # Try /app/nextflow-docs first (for Railway/Docker)
        if os.path.exists("/app"):
            target_dir = "/app/nextflow-docs"
        else:
            # Use temp directory for local dev
            target_dir = os.path.join(tempfile.gettempdir(), "nextflow-docs")
    
    # Check if docs already exist
    if os.path.exists(target_dir) and os.path.isdir(target_dir):
        # Check if it looks like Nextflow docs (has .md files)
        md_files = list(Path(target_dir).rglob("*.md"))
        if md_files:
            logger.info(f"Nextflow docs already exist at {target_dir}")
            return target_dir
    
    logger.info(f"Cloning Nextflow documentation from GitHub (branch: {branch})...")
    
    try:
        # Create parent directory if it doesn't exist
        parent_dir = os.path.dirname(os.path.abspath(target_dir))
        os.makedirs(parent_dir, exist_ok=True)
        
        # Remove target directory if it exists but is empty/invalid
        if os.path.exists(target_dir):
            shutil.rmtree(target_dir)
        
        # Clone the repository
        repo_url = "https://github.com/nextflow-io/nextflow.git"
        temp_clone = os.path.join(tempfile.gettempdir(), f"nextflow-clone-{os.getpid()}")
        
        try:
            logger.info(f"Cloning {repo_url} (branch: {branch}) to temporary location...")
            subprocess.run(
                ["git", "clone", "--depth", "1", "--branch", branch, repo_url, temp_clone],
                check=True,
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )
            
            # Move docs directory to target
            source_docs = os.path.join(temp_clone, "docs")
            if os.path.exists(source_docs):
                shutil.move(source_docs, target_dir)
                logger.info(f"✓ Nextflow docs cloned successfully to {target_dir}")
                return target_dir
            else:
                logger.warning(f"Docs directory not found in cloned repository at {source_docs}")
                return None
        finally:
            # Clean up temp clone directory
            if os.path.exists(temp_clone):
                shutil.rmtree(temp_clone, ignore_errors=True)
                
    except subprocess.TimeoutExpired:
        logger.error("Timeout cloning Nextflow docs (exceeded 5 minutes)")
        return None
    except subprocess.CalledProcessError as e:
        logger.error(f"Error cloning Nextflow docs: {e.stderr if e.stderr else str(e)}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error cloning Nextflow docs: {e}", exc_info=True)
        return None


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
    
    Always attempts to build if index is missing, regardless of CPU/GPU or docs availability.
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
    
    # Determine docs directory - use config if set, otherwise clone from GitHub
    docs_dir = config.NEXTFLOW_DOCS_DIR
    
    # If docs_dir is not set or doesn't exist, clone from GitHub
    if not docs_dir or not os.path.exists(docs_dir):
        logger.info("NEXTFLOW_DOCS_DIR not set or docs not found - cloning from GitHub...")
        cloned_docs_dir = clone_nextflow_docs()
        if cloned_docs_dir:
            docs_dir = cloned_docs_dir
            logger.info(f"Using cloned docs from {docs_dir}")
        else:
            logger.error("Failed to clone Nextflow docs from GitHub")
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

