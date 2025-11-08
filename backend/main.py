from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict
from contextlib import asynccontextmanager
from pathlib import Path
import os
import logging
from datetime import datetime
import uuid

# Set tokenizers parallelism to avoid fork warnings
os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")

# Suppress FAISS loader INFO messages before any imports
# Set this environment variable to prevent instruction set detection logs
os.environ.setdefault("FAISS_OPT_LEVEL", "")

# Setup logging - use INFO level for Railway (DEBUG shows as errors)
# Railway-friendly logging: only show INFO and above
log_level = os.environ.get('LOG_LEVEL', 'INFO').upper()
logging.basicConfig(
    level=getattr(logging, log_level, logging.INFO),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Suppress noisy INFO/DEBUG messages from third-party libraries
# Set these BEFORE importing the modules that use them
logging.getLogger('faiss.loader').setLevel(logging.WARNING)
logging.getLogger('pydantic._internal._fields').setLevel(logging.ERROR)
logging.getLogger('transformers').setLevel(logging.WARNING)
logging.getLogger('sentence_transformers').setLevel(logging.WARNING)
logging.getLogger('google.genai').setLevel(logging.WARNING)
logging.getLogger('google_genai').setLevel(logging.WARNING)
logging.getLogger('httpx').setLevel(logging.WARNING)
logging.getLogger('httpcore').setLevel(logging.WARNING)
logging.getLogger('urllib3').setLevel(logging.WARNING)
logging.getLogger('google.auth').setLevel(logging.WARNING)
logging.getLogger('google.auth.transport').setLevel(logging.WARNING)
logging.getLogger('google.oauth2').setLevel(logging.WARNING)
logging.getLogger('filelock').setLevel(logging.WARNING)

# Vector store imports - FAISS is lightweight, always try to import
# EmbeddingGenerator is lazy-loaded only when needed (for queries or building)
try:
    from vector_store.faiss_store import FAISSVectorStore
    from vector_store.document_loader import prepare_documents_for_indexing
    from vector_store.index_utils import check_index_exists, ensure_index_directory
    VECTOR_STORE_AVAILABLE = True
except ImportError as e:
    # Logger not yet defined, use print for import-time errors (will be rare)
    # This happens at module import time, before logging is configured
    import sys
    print(f"INFO: Vector store dependencies not available: {e}", file=sys.stdout)
    print("INFO: Running in LLM-only mode (no vector search)", file=sys.stdout)
    VECTOR_STORE_AVAILABLE = False
    FAISSVectorStore = None
    prepare_documents_for_indexing = None
    check_index_exists = None
    ensure_index_directory = None

from citations import CitationExtractor
from llm_client import LLMClient
import config

vector_store_instance: Optional[FAISSVectorStore] = None
citation_extractor: Optional[CitationExtractor] = None

def _initialize_vector_store():
    """Initialize vector store instance with lazy loading.
    
    Lazy-loads EmbeddingGenerator only when needed (for queries or building).
    Uses sentence-transformers for all embeddings (no Google API).
    """
    if not VECTOR_STORE_AVAILABLE:
        if logger.isEnabledFor(logging.DEBUG):
            logger.debug("Vector store dependencies not available - running in LLM-only mode")
        return None
    
    index_exists, index_path, _ = check_index_exists()
    
    if index_exists:
        logger.info(f"Index found at {index_path}")
    else:
        logger.info(f"Index not found at {index_path}")
        if logger.isEnabledFor(logging.DEBUG):
            logger.debug("  Index will be built if NEXTFLOW_DOCS_DIR is available")
    
    # Lazy import EmbeddingGenerator - always needed (for queries if index exists, or building if missing)
    # Only imported when actually needed to avoid loading heavy dependencies if vector store disabled
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


def _load_or_build_index(vector_store: Optional[FAISSVectorStore]):
    """Build index if it doesn't exist.
    
    Note: If index exists, it's already loaded by FAISSVectorStore.__init__.
    This function only handles building a new index from documentation.
    """
    if not vector_store or not VECTOR_STORE_AVAILABLE:
        logger.info("Vector store not available - running in LLM-only mode")
        return
    
    # Check if index is already loaded (was found and loaded by FAISSVectorStore.__init__)
    if vector_store.index is not None and vector_store.index.ntotal > 0:
        logger.info(f"Vector store ready: {vector_store.index.ntotal} vectors loaded")
        return
    
    # Index doesn't exist - try to build it
    index_exists, index_path, _ = check_index_exists()
    if index_exists:
        # Index exists but wasn't loaded - this shouldn't happen, but handle gracefully
        logger.warning(f"Index files exist at {index_path} but failed to load")
        return
    
    if logger.isEnabledFor(logging.DEBUG):
        logger.debug("Index not found - attempting to build from documentation...")
    
    # Ensure data directory exists
    ensure_index_directory(index_path)
    
    # Check if docs directory is available
    if not config.NEXTFLOW_DOCS_DIR or not os.path.exists(config.NEXTFLOW_DOCS_DIR):
        logger.info("NEXTFLOW_DOCS_DIR not set or docs not found - running in LLM-only mode")
        if logger.isEnabledFor(logging.DEBUG):
            logger.debug(f"  NEXTFLOW_DOCS_DIR: {config.NEXTFLOW_DOCS_DIR}")
            logger.debug("  To enable vector search: Set NEXTFLOW_DOCS_DIR or commit pre-built index files")
        return
    
    # Build index from documentation
    if logger.isEnabledFor(logging.DEBUG):
        logger.debug(f"Loading documents from: {config.NEXTFLOW_DOCS_DIR}")
    try:
        texts, metadata = prepare_documents_for_indexing(docs_dir=config.NEXTFLOW_DOCS_DIR)
        if texts:
            logger.info(f"Building index from {len(texts)} document chunks...")
            vector_store.build_index(texts, metadata)
            logger.info(f"Vector store built successfully: {len(texts)} chunks indexed")
        else:
            logger.warning("No documents loaded from docs directory - running in LLM-only mode")
    except Exception as e:
        logger.error(f"Error building vector store index: {e}", exc_info=True)
        logger.info("Failed to build index - running in LLM-only mode")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize vector store on startup (if available)."""
    global vector_store_instance, citation_extractor
    
    if VECTOR_STORE_AVAILABLE:
        logger.info("Initializing vector store...")
        try:
            vector_store_instance = _initialize_vector_store()
            if vector_store_instance:
                _load_or_build_index(vector_store_instance)
                # Verify vector store is actually ready (has loaded index)
                if vector_store_instance and vector_store_instance.index and vector_store_instance.index.ntotal > 0:
                    citation_extractor = CitationExtractor(vector_store_instance)
                    logger.info("Vector store ready!")
                else:
                    logger.info("Vector store initialized but index not loaded - running in LLM-only mode")
                    vector_store_instance = None
                    citation_extractor = CitationExtractor()
            else:
                logger.info("Vector store initialization failed - running in LLM-only mode")
                vector_store_instance = None
                citation_extractor = CitationExtractor()
        except Exception as e:
            logger.error(f"Error initializing vector store: {e}", exc_info=True)
            logger.info("Falling back to LLM-only mode")
            vector_store_instance = None
            citation_extractor = CitationExtractor()
    else:
        logger.info("Vector store dependencies not installed - running in LLM-only mode")
        vector_store_instance = None
        citation_extractor = CitationExtractor()
    
    yield
    logger.info("Shutting down...")

app = FastAPI(title="Nextflow Chat Assistant", lifespan=lifespan)

# CORS middleware - allow specific IP and Vercel domains
def is_allowed_origin(origin: str) -> bool:
    """Check if origin is allowed (IP address or Vercel domain)."""
    if not origin:
        return False
    
    # Allow IP address (with or without protocol)
    if "12.202.180.110" in origin:
        return True
    
    # Allow Vercel domains (*.vercel.app)
    if origin.endswith(".vercel.app"):
        return True
    
    # Allow common Vercel patterns
    if "vercel.app" in origin or "vercel.com" in origin:
        return True
    
    return False

# Get allowed origins from environment or use defaults
import re
cors_origins = os.environ.get("CORS_ORIGINS", "").split(",") if os.environ.get("CORS_ORIGINS") else []
cors_origins = [origin.strip() for origin in cors_origins if origin.strip()]

# Add default allowed origins
default_origins = [
    "http://12.202.180.110",
    "https://12.202.180.110",
    "http://12.202.180.110:3000",
    "https://12.202.180.110:3000",
    "http://12.202.180.110:80",
    "https://12.202.180.110:443",
]

# Combine and deduplicate
all_origins = list(set(default_origins + cors_origins))

app.add_middleware(
    CORSMiddleware,
    allow_origins=all_origins,
    allow_origin_regex=r"https?://.*\.vercel\.app.*",  # Allow any Vercel app domain
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)

# In-memory session storage
sessions: Dict[str, List[Dict]] = {}

# Request/Response models
class ChatMessage(BaseModel):
    message: str
    session_id: Optional[str] = None

class ChatResponse(BaseModel):
    reply: str
    session_id: str
    citations: Optional[List[str]] = None

def _format_context(results: List) -> str:
    """Format search results into context string."""
    context_parts = []
    seen_urls = set()
    
    for result in results:
        # Handle tuple format: (text, similarity, metadata)
        if isinstance(result, tuple) and len(result) >= 3:
            text, _, metadata = result[:3]
        else:
            continue
        
        # Ensure metadata is a dict
        if not isinstance(metadata, dict):
            metadata = {}
        
        context_parts.append(text)
        url = metadata.get('url')
        if url and url not in seen_urls:
            context_parts.append(f"Source: {url}")
            seen_urls.add(url)
    
    return "\n\n".join(context_parts)


def get_knowledge_context(query: str) -> str:
    """Retrieve relevant knowledge using vector store."""
    global vector_store_instance
    
    if not vector_store_instance:
        # Silent failure - vector store unavailable is expected in some deployments
        return ""
    
    try:
        import time
        start_time = time.time()
        
        results = vector_store_instance.search(
            query, 
            top_k=config.VECTOR_SEARCH_TOP_K,
            threshold=config.VECTOR_SEARCH_THRESHOLD
        )
        
        search_time = time.time() - start_time
        
        # Log summary only (detailed logs only in DEBUG mode)
        if logger.isEnabledFor(logging.DEBUG):
            logger.debug(f"Vector search for query: '{query[:100]}...' ({search_time:.3f}s)")
            logger.debug(f"Found {len(results)} results (top_k={config.VECTOR_SEARCH_TOP_K}, threshold={config.VECTOR_SEARCH_THRESHOLD})")
            for i, result in enumerate(results):
                if isinstance(result, tuple) and len(result) >= 3:
                    text, similarity, metadata = result[:3]
                    text_preview = text[:150] + "..." if len(text) > 150 else text
                    url = metadata.get('url', 'N/A') if isinstance(metadata, dict) else 'N/A'
                    logger.debug(f"  [{i+1}] Similarity: {similarity:.3f}, URL: {url}")
                    logger.debug(f"      Text: {text_preview}")
                else:
                    logger.debug(f"  [{i+1}] Result: {result}")
        elif results:
            # Brief summary for INFO level
            logger.info(f"Vector search: {len(results)} results found ({search_time:.3f}s)")
        
        return _format_context(results) if results else ""
    except Exception as e:
        logger.error(f"Error in vector store search: {e}", exc_info=True)
        return ""

def _get_system_prompt() -> str:
    """Get Nextflow-specific system prompt"""
    base_prompt = config.SYSTEM_PROMPT
    
    # Add max_output_tokens information to prompt
    max_tokens_info = f"\n\nIMPORTANT: Keep responses concise. You have a maximum output limit of {config.LLM_MAX_TOKENS} tokens. Be terse and focused in your responses."
    
    return f"{base_prompt}{max_tokens_info}"

def _build_messages(conversation_history: List[Dict], query: str, context: str) -> List[Dict]:
    """Build message list for LLM."""
    messages = []
    if conversation_history:
        for msg in conversation_history:
            messages.append({"role": msg["role"], "content": msg["content"]})
    
    user_message = query
    if context:
        user_message = f"Context from documentation:\n{context}\n\nUser question: {query}"
    
    messages.append({"role": "user", "content": user_message})
    return messages


async def call_gemini_direct(
    query: str, 
    conversation_history: Optional[List[Dict]] = None, 
    context: str = ""
) -> str:
    """Call Gemini directly via LLM client."""
    messages = _build_messages(conversation_history or [], query, context)
    system_prompt = _get_system_prompt()
    
    client = LLMClient()
    # google-genai client is synchronous, run in executor to avoid blocking
    import asyncio
    try:
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None, 
            lambda: client.complete(messages, system_prompt)
        )
    except Exception as e:
        # Only log the error message, not full stack trace (less verbose)
        logger.error(f"Error calling Gemini: {e}")
        raise

async def get_llm_response(
    query: str, 
    conversation_history: List[Dict], 
    context: str
) -> str:
    """Get response from LLM with context."""
    try:
        return await call_gemini_direct(query, conversation_history, context)
    except Exception as e:
        # Try fallback without context
        try:
            return await call_gemini_direct(query, conversation_history, "")
        except Exception as e2:
            # Only log final failure
            logger.error(f"LLM service unavailable: {e2}")
            raise HTTPException(
                status_code=500, 
                detail=f"LLM service unavailable: {str(e2)}"
            )

def _check_prompt_injection(message: str) -> bool:
    """
    Light guardrail to detect potential prompt injection attempts.
    Returns True if suspicious patterns are detected.
    """
    message_lower = message.lower()
    
    # Common prompt injection patterns
    suspicious_patterns = [
        "ignore previous instructions",
        "forget your role",
        "you are now",
        "act as",
        "pretend to be",
        "new instructions:",
        "override",
        "new system prompt",
        "previous prompt",
        "original prompt",
    ]
    
    # Check for suspicious patterns
    for pattern in suspicious_patterns:
        if pattern in message_lower:
            logger.warning(f"Potential prompt injection detected: pattern '{pattern}' in message")
            return True
    
    # Check for excessive role-playing attempts (multiple role indicators)
    role_indicators = message_lower.count("you are") + message_lower.count("you're")
    if role_indicators > 2:
        logger.warning(f"Potential prompt injection: excessive role indicators ({role_indicators})")
        return True
    
    return False


def _get_or_create_session(session_id: Optional[str]) -> str:
    """Get existing session or create new one."""
    if not session_id:
        session_id = str(uuid.uuid4())
    
    # Ensure session exists in dict
    if session_id not in sessions:
        sessions[session_id] = []
    
    return session_id


def _add_user_message(session_id: str, message: str):
    """Add user message to session."""
    sessions[session_id].append({
        "role": "user",
        "content": message,
        "timestamp": datetime.now().isoformat()
    })


def _add_assistant_message(session_id: str, reply: str):
    """Add assistant message to session."""
    sessions[session_id].append({
        "role": "assistant",
        "content": reply,
        "timestamp": datetime.now().isoformat()
    })


def _get_citations(query: str) -> Optional[List[str]]:
    """Get citations for query from vector store, with fallback to empty."""
    if not citation_extractor:
        return
    return citation_extractor.extract_from_query(query)


@app.post("/chat", response_model=ChatResponse)
async def chat(message: ChatMessage):
    """Main chat endpoint."""
    try:
        # Validate message
        if not message.message or not message.message.strip():
            raise HTTPException(
                status_code=400,
                detail="Message cannot be empty"
            )
        
        # Validate input length
        input_length = len(message.message)
        if input_length > config.MAX_INPUT_LENGTH:
            raise HTTPException(
                status_code=400,
                detail=f"Input message is too large ({input_length:,} characters). Maximum allowed is {config.MAX_INPUT_LENGTH:,} characters."
            )
        
        # Light guardrail: check for prompt injection attempts
        if _check_prompt_injection(message.message):
            # Log but don't block - let the LLM handle it with its system prompt
            # This is a lightweight guardrail that just raises awareness
            # Log at debug level only - not an error, just informational
            if logger.isEnabledFor(logging.DEBUG):
                logger.debug("Prompt injection pattern detected, but allowing through (LLM system prompt should handle)")
        
        session_id = _get_or_create_session(message.session_id)
        
        # Ensure session exists (safety check)
        if session_id not in sessions:
            sessions[session_id] = []
        
        # Get conversation history (excluding the message we're about to add)
        conversation_history = sessions[session_id].copy()
        
        # Add user message to session
        _add_user_message(session_id, message.message)
        
        # Get context and generate reply
        context = get_knowledge_context(message.message)
        reply = await get_llm_response(
            message.message, 
            conversation_history, 
            context
        )
        
        _add_assistant_message(session_id, reply)
        citations = _get_citations(message.message)
        # Always return citations (either from vector store or defaults)
        
        return ChatResponse(
            reply=reply,
            session_id=session_id,
            citations=citations
        )
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        logger.error(f"Error processing chat: {e}", exc_info=True)
        raise HTTPException(
            status_code=500, 
            detail=f"Error processing chat: {str(e)}"
        )

@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "ok"}

