#!/usr/bin/env python3
"""
Check if vector index exists and report status.
Used in Dockerfile to determine if index needs to be built.
"""
import os
import sys
from pathlib import Path

# Add parent directory to path to import config
sys.path.insert(0, str(Path(__file__).parent))

try:
    from vector_store.index_utils import check_index_exists
except ImportError:
    # Fallback if vector_store not available (shouldn't happen in Docker, but handle gracefully)
    try:
        import config
    except ImportError:
        print("ERROR: Could not import config.py", file=sys.stderr)
        sys.exit(1)
    
    def check_index_exists():
        index_path = config.VECTOR_INDEX_PATH
        data_path = index_path.replace('.index', '.data')
        exists = os.path.exists(index_path) and os.path.exists(data_path)
        return exists, index_path, data_path


def check_index():
    """Check if vector index exists and return exit code.
    
    Returns:
        0 if index exists, 1 if index doesn't exist
    """
    index_exists, index_path, data_path = check_index_exists()
    
    if index_exists:
        # Check file sizes
        index_size = os.path.getsize(index_path) / (1024 * 1024)  # MB
        data_size = os.path.getsize(data_path) / (1024 * 1024)  # MB
        print(f"✓ Index found at {index_path}")
        print(f"  Index size: {index_size:.2f} MB")
        print(f"  Data size: {data_size:.2f} MB")
        return 0
    else:
        print(f"✗ Index not found at {index_path}")
        print("  Index will be built during Docker build")
        return 1


if __name__ == "__main__":
    exit_code = check_index()
    sys.exit(exit_code)

