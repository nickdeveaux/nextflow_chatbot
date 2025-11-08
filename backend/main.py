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

# Setup logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Vector store imports - FAISS is lightweight, always try to import
# EmbeddingGenerator is lazy-loaded only when needed (for queries or building)
try:
    from vector_store.faiss_store import FAISSVectorStore
    from vector_store.document_loader import prepare_documents_for_indexing
    from vector_store.index_utils import check_index_exists, ensure_index_directory
    VECTOR_STORE_AVAILABLE = True
except ImportError as e:
    print(f"Vector store dependencies not available: {e}")
    print("Running in LLM-only mode (no vector search)")
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
        return None
    
    index_exists, index_path, _ = check_index_exists()
    
    if index_exists:
        print(f"✓ Index found at {index_path}")
    else:
        print(f"✗ Index not found at {index_path}")
        print("  Index will be built if NEXTFLOW_DOCS_DIR is available")
    
    # Lazy import EmbeddingGenerator - always needed (for queries if index exists, or building if missing)
    # Only imported when actually needed to avoid loading heavy dependencies if vector store disabled
    try:
        from vector_store.embeddings import EmbeddingGenerator
        embedding_gen = EmbeddingGenerator()
    except ImportError as e:
        if index_exists:
            logger.warning(f"sentence-transformers not available: {e}")
            logger.warning("Vector search requires sentence-transformers for query embeddings")
        else:
            logger.error(f"sentence-transformers not available: {e}")
            logger.error("Cannot build index. Install with: pip install -r requirements-build-index.txt")
        return None
    except Exception as e:
        logger.error(f"Error initializing embedding generator: {e}")
        return None
    
    try:
        return FAISSVectorStore(embedding_gen, index_path=index_path)
    except Exception as e:
        logger.error(f"Error creating FAISSVectorStore: {e}")
        return None


def _load_or_build_index(vector_store: Optional[FAISSVectorStore]):
    """Build index if it doesn't exist.
    
    Note: If index exists, it's already loaded by FAISSVectorStore.__init__.
    This function only handles building a new index from documentation.
    """
    if not vector_store or not VECTOR_STORE_AVAILABLE:
        print("Vector store not available - running in LLM-only mode")
        return
    
    # Check if index is already loaded (was found and loaded by FAISSVectorStore.__init__)
    if vector_store.index is not None and vector_store.index.ntotal > 0:
        print(f"✓ Vector store ready: {vector_store.index.ntotal} vectors loaded")
        return
    
    # Index doesn't exist - try to build it
    index_exists, index_path, _ = check_index_exists()
    if index_exists:
        # Index exists but wasn't loaded - this shouldn't happen, but handle gracefully
        print(f"Warning: Index files exist at {index_path} but failed to load")
        return
    
    print("Index not found - attempting to build from documentation...")
    
    # Ensure data directory exists
    ensure_index_directory(index_path)
    
    # Check if docs directory is available
    if not config.NEXTFLOW_DOCS_DIR or not os.path.exists(config.NEXTFLOW_DOCS_DIR):
        print(f"  NEXTFLOW_DOCS_DIR not set or docs not found: {config.NEXTFLOW_DOCS_DIR}")
        print("  Running in LLM-only mode (no vector search)")
        print("  To enable vector search:")
        print("    1. Set NEXTFLOW_DOCS_DIR environment variable")
        print("    2. Or commit pre-built index files to repository")
        return
    
    # Build index from documentation
    print(f"  Loading documents from: {config.NEXTFLOW_DOCS_DIR}")
    try:
        texts, metadata = prepare_documents_for_indexing(docs_dir=config.NEXTFLOW_DOCS_DIR)
        if texts:
            print(f"  Building index from {len(texts)} document chunks...")
            vector_store.build_index(texts, metadata)
            print(f"✓ Vector store built successfully: {len(texts)} chunks indexed")
        else:
            print("  Warning: No documents loaded from docs directory")
            print("  Running in LLM-only mode")
    except Exception as e:
        logger.error(f"Error building vector store index: {e}")
        print("  Failed to build index - running in LLM-only mode")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize vector store on startup (if available)."""
    global vector_store_instance, citation_extractor
    
    if VECTOR_STORE_AVAILABLE:
        print("Initializing vector store...")
        try:
            vector_store_instance = _initialize_vector_store()
            _load_or_build_index(vector_store_instance)
            citation_extractor = CitationExtractor(vector_store_instance)
            print("Vector store ready!")
        except Exception as e:
            print(f"Error initializing vector store: {e}")
            print("Falling back to LLM-only mode")
            vector_store_instance = None
            citation_extractor = CitationExtractor()
    else:
        print("Vector store dependencies not installed - running in LLM-only mode")
        vector_store_instance = None
        citation_extractor = CitationExtractor()
    
    yield
    print("Shutting down...")

app = FastAPI(title="Nextflow Chat Assistant", lifespan=lifespan)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your frontend URL
    allow_credentials=True,
    allow_methods=["*"],
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
        logger.debug("Vector store not initialized, returning empty context")
        return ""
    
    try:
        results = vector_store_instance.search(
            query, 
            top_k=config.VECTOR_SEARCH_TOP_K,
            threshold=config.VECTOR_SEARCH_THRESHOLD
        )
        
        # Log retrieved documents
        logger.debug(f"Vector search for query: '{query[:100]}...'")
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
        import traceback
        print(f"Error calling Gemini: {e}")
        print(f"Traceback: {traceback.format_exc()}")
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
        print(f"Error in get_llm_response: {e}")
        try:
            return await call_gemini_direct(query, conversation_history, "")
        except Exception as e2:
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
            logger.info("Prompt injection pattern detected, but allowing through (LLM system prompt should handle)")
        
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
        print(f"Error processing chat: {e}")
        print(traceback.format_exc())
        raise HTTPException(
            status_code=500, 
            detail=f"Error processing chat: {str(e)}"
        )

@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "ok"}

