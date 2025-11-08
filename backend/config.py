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
_CONFIG_PATH = Path(__file__).parent.parent / "config.yaml"
with open(_CONFIG_PATH, 'r') as f:
    _config = yaml.safe_load(f)

SERVICE_ACCOUNT_PATH = os.getenv(
    "SERVICE_ACCOUNT_PATH",
   str(_config['api'].get('service_account_path'))
)

if not SERVICE_ACCOUNT_PATH and os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON"):
    with tempfile.NamedTemporaryFile("w", delete=False, suffix=".json") as f:
        f.write(os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON"))
        SERVICE_ACCOUNT_PATH = f.name
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

