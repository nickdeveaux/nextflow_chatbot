#!/usr/bin/env python3
"""
Check if vector index exists and report status.
"""
import os
import sys
from pathlib import Path

# Add parent directory to path to import config
sys.path.insert(0, str(Path(__file__).parent))

try:
    from vector_store.index_utils import check_index_exists
except ImportError:
    # Fallback if vector_store not available
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
    """Check if vector index exists and print status."""
    index_exists, index_path, data_path = check_index_exists()
    
    print(f"Index path: {index_path}")
    print(f"Data path: {data_path}")
    print(f"Index exists: {index_exists}")
    
    if index_exists:
        # Check file sizes
        index_size = os.path.getsize(index_path) / (1024 * 1024)  # MB
        data_size = os.path.getsize(data_path) / (1024 * 1024)  # MB
        print(f"Index size: {index_size:.2f} MB")
        print(f"Data size: {data_size:.2f} MB")
        print("\n✓ Index files found - ready for vector search")
        return 0
    else:
        print("\n✗ Index files not found")
        print("  To build index: Set BUILD_INDEX=true and NEXTFLOW_DOCS_DIR")
        print("  Or commit pre-built index files to repository")
        return 1


if __name__ == "__main__":
    exit_code = check_index()
    sys.exit(exit_code)

