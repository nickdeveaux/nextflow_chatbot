"""
Configuration for Nextflow Chat Assistant backend.
Loads from shared config.yaml with environment variable overrides.
Minimal logic - most defaults and structure are in config.yaml.
"""
import os
import yaml
from pathlib import Path
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

# Helper function to get config value with env override
def _get_config(section: dict, key: str, env_key: str = None, default=None, type_fn=None):
    """Get config value with environment variable override."""
    env_key = env_key or key.upper()
    env_val = os.getenv(env_key)
    if env_val is not None:
        return type_fn(env_val) if type_fn else env_val
    yaml_val = section.get(key, default)
    return type_fn(yaml_val) if type_fn and yaml_val is not None else yaml_val

# Service Account Configuration
# Priority: GOOGLE_SERVICE_ACCOUNT_JSON (env) > SERVICE_ACCOUNT_PATH (env) > config.yaml
SERVICE_ACCOUNT_PATH = None
google_json = os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON")
if google_json and google_json.strip():
    try:
        with tempfile.NamedTemporaryFile("w", delete=False, suffix=".json") as f:
            f.write(google_json)
            SERVICE_ACCOUNT_PATH = f.name
            os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = SERVICE_ACCOUNT_PATH
    except Exception as e:
        raise ValueError(f"Failed to create service account file from GOOGLE_SERVICE_ACCOUNT_JSON: {e}")
else:
    _service_account_path = _get_config(
        _config.get('api', {}), 
        'service_account_path', 
        'SERVICE_ACCOUNT_PATH',
        ''
    )
    if _service_account_path and _service_account_path.strip():
        SERVICE_ACCOUNT_PATH = _service_account_path.strip()
        if SERVICE_ACCOUNT_PATH and not os.path.exists(SERVICE_ACCOUNT_PATH):
            pass  # Let LLM client handle the error
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = SERVICE_ACCOUNT_PATH

# LLM Configuration
_llm_config = _config.get('llm', {})
LLM_MODEL = _get_config(_llm_config, 'model', 'LLM_MODEL', 'gemini-2.0-flash-exp')
LLM_TEMPERATURE = _get_config(_llm_config, 'temperature', 'LLM_TEMPERATURE', 0.7, float)
LLM_MAX_TOKENS = _get_config(_llm_config, 'max_tokens', 'LLM_MAX_TOKENS', 1000, int)
MAX_INPUT_LENGTH = _get_config(_llm_config, 'max_input_length', 'MAX_INPUT_LENGTH', 500000, int)

# Vector Store Configuration
_vector_config = _config.get('vector_store', {})
NEXTFLOW_DOCS_DIR = _get_config(_vector_config, 'nextflow_docs_dir', 'NEXTFLOW_DOCS_DIR', '').strip()

# Index path resolution: env > yaml > container default > local default
_yaml_index_path = _get_config(_vector_config, 'index_path', 'VECTOR_INDEX_PATH', '')
if _yaml_index_path:
    VECTOR_INDEX_PATH = _yaml_index_path
elif os.path.exists('/app'):  # Running in container
    VECTOR_INDEX_PATH = '/app/data/vector_index.index'
else:  # Local development
    VECTOR_INDEX_PATH = './vector_index.index'

VECTOR_SEARCH_TOP_K = _get_config(_vector_config, 'search_top_k', 'VECTOR_SEARCH_TOP_K', 5, int)
VECTOR_SEARCH_THRESHOLD = _get_config(_vector_config, 'search_threshold', 'VECTOR_SEARCH_THRESHOLD', 0.4, float)

# System Prompt
SYSTEM_PROMPT = _config.get('system_prompt', '').strip()

# CORS Configuration
_cors_config = _config.get('cors', {})
_cors_origins_env = os.getenv("CORS_ORIGINS", "")
CORS_ALLOWED_ORIGINS = (
    [origin.strip() for origin in _cors_origins_env.split(",") if origin.strip()]
    if _cors_origins_env
    else _cors_config.get('allowed_origins', [])
)

CORS_ALLOW_VERCEL_DOMAINS = _get_config(
    _cors_config, 'allow_vercel_domains', 'CORS_ALLOW_VERCEL_DOMAINS', True
)
# Convert to bool if string
if isinstance(CORS_ALLOW_VERCEL_DOMAINS, str):
    CORS_ALLOW_VERCEL_DOMAINS = CORS_ALLOW_VERCEL_DOMAINS.lower() in ('true', '1', 'yes', 'on')

CORS_VERCEL_DOMAIN_REGEX = _get_config(
    _cors_config, 'vercel_domain_regex', 'CORS_VERCEL_DOMAIN_REGEX', r"https?://.*\.vercel\.app.*"
)

CORS_ALLOW_CREDENTIALS = _get_config(
    _cors_config, 'allow_credentials', 'CORS_ALLOW_CREDENTIALS', True
)
# Convert to bool if string
if isinstance(CORS_ALLOW_CREDENTIALS, str):
    CORS_ALLOW_CREDENTIALS = CORS_ALLOW_CREDENTIALS.lower() in ('true', '1', 'yes', 'on')

CORS_ALLOWED_METHODS = _cors_config.get('allowed_methods', ["GET", "POST", "OPTIONS"])
if os.getenv("CORS_ALLOWED_METHODS"):
    CORS_ALLOWED_METHODS = [m.strip() for m in os.getenv("CORS_ALLOWED_METHODS").split(",")]

CORS_ALLOWED_HEADERS = _cors_config.get('allowed_headers', ["*"])
if os.getenv("CORS_ALLOWED_HEADERS"):
    CORS_ALLOWED_HEADERS = [h.strip() for h in os.getenv("CORS_ALLOWED_HEADERS").split(",")]
