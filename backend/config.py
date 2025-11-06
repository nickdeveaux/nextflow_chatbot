"""
Configuration for Nextflow Chat Assistant backend.
Loads from shared config.yaml with environment variable overrides.
"""
import os
import yaml
from pathlib import Path
from typing import List

# Load YAML config
_CONFIG_PATH = Path(__file__).parent.parent / "config.yaml"
with open(_CONFIG_PATH, 'r') as f:
    _config = yaml.safe_load(f)

# API Configuration (env var overrides YAML)
GOOGLE_VERTEX_API_KEY = os.getenv(
    "GOOGLE_VERTEX_API_KEY",
    _config['api']['google_vertex_api_key']
)
GOOGLE_CLOUD_PROJECT = os.getenv(
    "GOOGLE_CLOUD_PROJECT",
    os.getenv("GCP_PROJECT", _config['api'].get('google_cloud_project', ''))
)

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

# Vector Store Configuration (env var overrides YAML)
NEXTFLOW_DOCS_DIR = os.getenv(
    "NEXTFLOW_DOCS_DIR",
    _config['vector_store']['nextflow_docs_dir']
)
VECTOR_INDEX_PATH = os.getenv(
    "VECTOR_INDEX_PATH",
    _config['vector_store']['index_path']
)
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

# Default Citations (from YAML)
DEFAULT_CITATIONS = _config['default_citations']

