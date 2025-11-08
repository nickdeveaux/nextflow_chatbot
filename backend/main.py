"""
FastAPI application for Nextflow Chat Assistant.
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from typing import Optional
import os
import asyncio
import logging

# Set tokenizers parallelism to avoid fork warnings
os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")
os.environ.setdefault("FAISS_OPT_LEVEL", "")

# Setup logging first
from logging_config import setup_logging
logger = setup_logging()

# Import refactored modules
from models import ChatMessage, ChatResponse
from session_manager import (
    get_or_create_session, add_user_message, add_assistant_message,
    get_conversation_history
)
from security import check_prompt_injection
from llm_utils import get_system_prompt, build_messages
from context_formatter import format_context
from vector_store_manager import initialize_vector_store, load_or_build_index, VECTOR_STORE_AVAILABLE
from citations import CitationExtractor
from llm_client import LLMClient
import config

# Global state
vector_store_instance = None
citation_extractor: Optional[CitationExtractor] = None


def get_knowledge_context(query: str) -> str:
    """Retrieve relevant knowledge using vector store."""
    global vector_store_instance
    
    if not vector_store_instance:
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
            logger.info(f"Vector search: {len(results)} results found ({search_time:.3f}s)")
        
        return format_context(results) if results else ""
    except Exception as e:
        logger.error(f"Error in vector store search: {e}", exc_info=True)
        return ""


async def call_gemini_direct(
    query: str, 
    conversation_history: list = None, 
    context: str = ""
) -> str:
    """Call Gemini directly via LLM client."""
    messages = build_messages(conversation_history or [], query, context)
    system_prompt = get_system_prompt()
    
    client = LLMClient()
    # google-genai client is synchronous, run in executor to avoid blocking
    try:
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None, 
            lambda: client.complete(messages, system_prompt)
        )
    except Exception as e:
        logger.error(f"Error calling Gemini: {e}")
        raise


async def get_llm_response(
    query: str, 
    conversation_history: list, 
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
            logger.error(f"LLM service unavailable: {e2}")
            raise HTTPException(
                status_code=500, 
                detail=f"LLM service unavailable: {str(e2)}"
            )


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize vector store on startup (if available)."""
    global vector_store_instance, citation_extractor
    
    if VECTOR_STORE_AVAILABLE:
        logger.info("Initializing vector store...")
        try:
            vector_store_instance = initialize_vector_store()
            if vector_store_instance:
                load_or_build_index(vector_store_instance)
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

# CORS middleware - configured from config.yaml
cors_kwargs = {
    "allow_origins": config.CORS_ALLOWED_ORIGINS,
    "allow_credentials": config.CORS_ALLOW_CREDENTIALS,
    "allow_methods": config.CORS_ALLOWED_METHODS,
    "allow_headers": config.CORS_ALLOWED_HEADERS,
}

# Add Vercel domain regex if enabled (from config.yaml)
if config.CORS_ALLOW_VERCEL_DOMAINS:
    cors_kwargs["allow_origin_regex"] = config.CORS_VERCEL_DOMAIN_REGEX

app.add_middleware(
    CORSMiddleware,
    **cors_kwargs
)


def get_citations(query: str) -> Optional[list]:
    """Get citations for query from vector store, with fallback to empty."""
    global citation_extractor
    if not citation_extractor:
        return None
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
        if check_prompt_injection(message.message):
            if logger.isEnabledFor(logging.DEBUG):
                logger.debug("Prompt injection pattern detected, but allowing through (LLM system prompt should handle)")
        
        session_id = get_or_create_session(message.session_id)
        
        # Get conversation history (excluding the message we're about to add)
        conversation_history = get_conversation_history(session_id)
        
        # Add user message to session
        add_user_message(session_id, message.message)
        
        # Get context and generate reply
        context = get_knowledge_context(message.message)
        reply = await get_llm_response(
            message.message, 
            conversation_history, 
            context
        )
        
        add_assistant_message(session_id, reply)
        citations = get_citations(message.message)
        
        return ChatResponse(
            reply=reply,
            session_id=session_id,
            citations=citations
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing chat: {e}", exc_info=True)
        raise HTTPException(
            status_code=500, 
            detail=f"Error processing chat: {str(e)}"
        )


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "ok"}
