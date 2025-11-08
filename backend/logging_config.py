"""
Logging configuration for Railway-friendly output.
Suppresses third-party library noise while preserving app logs.
"""
import os
import logging
import sys
import warnings

# Suppress Python warnings (they show as errors in Railway)
warnings.filterwarnings('ignore')
warnings.filterwarnings('ignore', category=DeprecationWarning)
warnings.filterwarnings('ignore', category=UserWarning)
warnings.filterwarnings('ignore', category=FutureWarning)


class RailwayLogFilter(logging.Filter):
    """Filter to suppress third-party library logs in Railway."""
    # Third-party library prefixes to suppress (unless ERROR level)
    SUPPRESSED_PREFIXES = (
        'transformers', 'sentence_transformers', 'faiss', 'pydantic',
        'google', 'google_genai', 'httpx', 'httpcore', 'urllib3',
        'huggingface_hub', 'torch', 'tokenizers', 'tqdm', 'filelock'
    )
    
    def filter(self, record):
        # Always show our app logs
        if record.name in ('main', 'llm_client', '__main__') or record.name.startswith('backend'):
            return True
        # Always show ERROR level and above
        if record.levelno >= logging.ERROR:
            return True
        # Block third-party libraries below ERROR level
        if any(record.name.startswith(prefix) for prefix in self.SUPPRESSED_PREFIXES):
            return False
        # Allow other logs (unknown modules) at INFO and above
        return record.levelno >= logging.INFO


def setup_logging():
    """Configure logging for Railway-friendly output."""
    # Set up logging - INFO level by default (DEBUG shows as errors in Railway)
    # Railway treats stderr as errors, so we route everything to stdout
    log_level = os.environ.get('LOG_LEVEL', 'INFO').upper()
    logging.basicConfig(
        level=getattr(logging, log_level, logging.INFO),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        stream=sys.stdout,  # Explicitly use stdout (Railway treats stderr as errors)
        force=True  # Override any existing configuration
    )
    
    # Apply filter to root handler
    root_logger = logging.getLogger()
    for handler in root_logger.handlers:
        handler.addFilter(RailwayLogFilter())
    
    # Suppress ALL third-party library logging below WARNING level
    third_party_loggers = [
        'faiss', 'faiss.loader',
        'pydantic', 'pydantic._internal', 'pydantic._internal._fields',
        'transformers', 'transformers.configuration_utils',
        'transformers.tokenization_utils_base', 'transformers.modeling_utils',
        'sentence_transformers', 'sentence_transformers.SentenceTransformer',
        'google', 'google.genai', 'google_genai',
        'google.auth', 'google.auth.transport', 'google.auth.transport.requests',
        'google.oauth2', 'google.oauth2.service_account',
        'httpx', 'httpcore', 'httpcore.http11', 'httpcore.connection',
        'urllib3', 'urllib3.connectionpool',
        'filelock', 'huggingface_hub', 'torch', 'torch.nn', 'torch.optim',
        'tokenizers', 'tqdm',
    ]
    
    for logger_name in third_party_loggers:
        third_party_logger = logging.getLogger(logger_name)
        third_party_logger.setLevel(logging.WARNING)
        # Also disable propagation to prevent messages from bubbling up
        third_party_logger.propagate = False
    
    # Ensure our app logs are visible
    logging.getLogger('main').setLevel(logging.INFO)
    logging.getLogger('llm_client').setLevel(logging.INFO)
    
    return logging.getLogger(__name__)

