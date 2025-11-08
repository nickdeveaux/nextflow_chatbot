"""
Logging configuration for Railway-friendly output.
Suppresses third-party library noise while preserving app logs.
"""
import os
import logging
import sys
import warnings

# Suppress Python warnings (they show as errors in Railway)
warnings.filterwarnings('ignore', category=DeprecationWarning)
warnings.filterwarnings('ignore', category=UserWarning)
warnings.filterwarnings('ignore', category=FutureWarning)


class InfoFilter(logging.Filter):
    """Filter to route DEBUG and INFO logs to stdout."""
    def filter(self, rec):
        return rec.levelno in (logging.DEBUG, logging.INFO)


def setup_logging():
    """Configure logging with correct output streams.
    
    DEBUG and INFO logs → stdout (Railway shows as normal logs)
    WARNING and above → stderr (Railway shows as errors, which is correct)
    """
    # Get log level from environment (default: INFO)
    log_level = os.environ.get('LOG_LEVEL', 'INFO').upper()
    level = getattr(logging, log_level, logging.INFO)
    
    # Get root logger
    logger = logging.getLogger()
    logger.setLevel(level)
    
    # Remove any existing handlers
    logger.handlers.clear()
    
    # Handler 1: stdout for DEBUG and INFO
    h1 = logging.StreamHandler(sys.stdout)
    h1.setLevel(logging.DEBUG)
    h1.addFilter(InfoFilter())
    h1.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    
    # Handler 2: stderr for WARNING and above
    h2 = logging.StreamHandler(sys.stderr)
    h2.setLevel(logging.WARNING)
    h2.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    
    # Add both handlers
    logger.addHandler(h1)
    logger.addHandler(h2)
    
    # Suppress third-party library logging below WARNING level
    # This prevents verbose logs from showing up
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
        third_party_logger.propagate = False
    
    # Return app logger for convenience
    app_logger = logging.getLogger('main')
    app_logger.setLevel(level)
    
    return app_logger

