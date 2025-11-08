"""
Configuration for Nextflow Chat Assistant backend.
Loads from shared config.yaml with environment variable overrides.
"""
import os
import yaml
from pathlib import Path
from typing import List
import tempfile

# Load YAML config
# Try multiple possible locations (check container path first for Railway):
# 1. Absolute path in container: /app/config.yaml
# 2. Same directory as config.py (for container: /app/config.yaml)
# 3. Parent directory (for local: backend/../config.yaml)
_CONFIG_PATH = None
possible_paths = [
    Path("/app/config.yaml"),  # Absolute path in container (Railway)
    Path(__file__).parent / "config.yaml",  # Same directory as config.py
    Path(__file__).parent.parent / "config.yaml",  # Parent directory (local dev)
]
for path in possible_paths:
    if path.exists():
        _CONFIG_PATH = path
        break

if _CONFIG_PATH is None:
    raise FileNotFoundError(
        f"config.yaml not found. Tried: {', '.join(str(p) for p in possible_paths)}"
    )

with open(_CONFIG_PATH, 'r') as f:
    _config = yaml.safe_load(f)

# Priority order for service account:
# 1. GOOGLE_SERVICE_ACCOUNT_JSON (env var with JSON content) - create temp file
# 2. SERVICE_ACCOUNT_PATH (env var with file path)
# 3. config.yaml value (fallback)
SERVICE_ACCOUNT_PATH = None

# First, check if JSON content is provided (Railway secret - highest priority)
google_json = os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON")
if google_json and google_json.strip():
    try:
        with tempfile.NamedTemporaryFile("w", delete=False, suffix=".json") as f:
            f.write(google_json)
            SERVICE_ACCOUNT_PATH = f.name
            os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = SERVICE_ACCOUNT_PATH
    except Exception as e:
        raise ValueError(f"Failed to create service account file from GOOGLE_SERVICE_ACCOUNT_JSON: {e}")
# Otherwise, check for file path (env var or config.yaml)
else:
    _service_account_path = os.getenv("SERVICE_ACCOUNT_PATH")
    if not _service_account_path or not _service_account_path.strip():
        # Fall back to config.yaml
        _service_account_path = str(_config['api'].get('service_account_path', '') or '')
    
    if _service_account_path and _service_account_path.strip():
        SERVICE_ACCOUNT_PATH = _service_account_path.strip()
        # Verify file exists if it's not an empty string
        if SERVICE_ACCOUNT_PATH and not os.path.exists(SERVICE_ACCOUNT_PATH):
            # Don't fail here - let the LLM client handle the error with a better message
            pass
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = SERVICE_ACCOUNT_PATH

# LLM Configuration (env var overrides YAML)
LLM_MODEL = os.getenv("LLM_MODEL", _config['llm']['model'])
LLM_TEMPERATURE = float(os.getenv(
    "LLM_TEMPERATURE", 
    str(_config['llm']['temperature'])
))
LLM_MAX_TOKENS = int(os.getenv(
    "LLM_MAX_TOKENS", 
    str(_config['llm']['max_tokens'])
))
MAX_INPUT_LENGTH = int(os.getenv(
    "MAX_INPUT_LENGTH",
    str(_config['llm'].get('max_input_length'))
))

# Vector Store Configuration (env var overrides YAML)
# For Railway: Use /app/data for persistent storage
# For local: Use ./vector_index.index in current directory
# If NEXTFLOW_DOCS_DIR is empty or not set, vector store will work in LLM-only mode
NEXTFLOW_DOCS_DIR = os.getenv(
    "NEXTFLOW_DOCS_DIR",
    _config['vector_store'].get('nextflow_docs_dir', '') or ''
).strip()

# Smart default: Use /app/data in container (Railway), ./vector_index.index for local
_yaml_index_path = _config['vector_store'].get('index_path', '')
if _yaml_index_path:
    _default_index_path = _yaml_index_path
elif os.path.exists('/app'):  # Running in container
    _default_index_path = '/app/data/vector_index.index'
else:  # Local development
    _default_index_path = './vector_index.index'

VECTOR_INDEX_PATH = os.getenv("VECTOR_INDEX_PATH", _default_index_path)
VECTOR_SEARCH_TOP_K = int(os.getenv(
    "VECTOR_SEARCH_TOP_K",
    str(_config['vector_store']['search_top_k'])
))
VECTOR_SEARCH_THRESHOLD = float(os.getenv(
    "VECTOR_SEARCH_THRESHOLD",
    str(_config['vector_store']['search_threshold'])
))

# System Prompt (from YAML)
SYSTEM_PROMPT = _config['system_prompt'].strip()

