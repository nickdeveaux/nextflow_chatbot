"""
Utility functions for vector index management.
"""
import os
import config


def check_index_exists():
    """Check if vector index files exist.
    
    Returns:
        tuple: (exists: bool, index_path: str, data_path: str)
    """
    index_path = config.VECTOR_INDEX_PATH
    data_path = index_path.replace('.index', '.data')
    exists = os.path.exists(index_path) and os.path.exists(data_path)
    return exists, index_path, data_path


def ensure_index_directory(index_path: str):
    """Ensure the directory for the index file exists.
    
    Args:
        index_path: Path to the index file
    """
    index_dir = os.path.dirname(os.path.abspath(index_path))
    if index_dir and not os.path.exists(index_dir):
        os.makedirs(index_dir, exist_ok=True)

