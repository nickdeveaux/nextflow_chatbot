from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict
from contextlib import asynccontextmanager
import os
from datetime import datetime
import uuid

# Set tokenizers parallelism to avoid fork warnings
os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")

from vector_store.embeddings import EmbeddingGenerator
from vector_store.faiss_store import FAISSVectorStore
from vector_store.document_loader import prepare_documents_for_indexing
from citations import CitationExtractor
from llm_client import LLMClient
import config

vector_store_instance: Optional[FAISSVectorStore] = None
citation_extractor: Optional[CitationExtractor] = None

def _initialize_vector_store():
    """Initialize vector store instance."""
    embedding_gen = EmbeddingGenerator()
    return FAISSVectorStore(
        embedding_gen, 
        index_path=config.VECTOR_INDEX_PATH
    )


def _load_or_build_index(vector_store: FAISSVectorStore):
    """Load existing index or build new one."""
    data_path = config.VECTOR_INDEX_PATH.replace('.index', '.data')
    
    if os.path.exists(config.VECTOR_INDEX_PATH) and os.path.exists(data_path):
        print("Loading existing vector store index...")
        vector_store.load(config.VECTOR_INDEX_PATH)
    else:
        print("Building vector store index from documentation...")
        texts, metadata = prepare_documents_for_indexing(
            docs_dir=config.NEXTFLOW_DOCS_DIR
        )
        if texts:
            vector_store.build_index(texts, metadata)
            print(f"Vector store initialized with {len(texts)} chunks")
        else:
            print("Warning: No documents loaded.")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize vector store on startup."""
    global vector_store_instance, citation_extractor
    
    print("Initializing vector store...")
    try:
        vector_store_instance = _initialize_vector_store()
        _load_or_build_index(vector_store_instance)
        citation_extractor = CitationExtractor(vector_store_instance)
        print("Vector store ready!")
    except Exception as e:
        print(f"Error initializing vector store: {e}")
        vector_store_instance = None
        citation_extractor = CitationExtractor()
    
    yield
    print("Shutting down vector store...")

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
        return ""
    
    try:
        results = vector_store_instance.search(
            query, 
            top_k=config.VECTOR_SEARCH_TOP_K,
            threshold=config.VECTOR_SEARCH_THRESHOLD
        )
        return _format_context(results) if results else ""
    except Exception as e:
        print(f"Error in vector store search: {e}")
        return ""

def _get_system_prompt() -> str:
    """Get Nextflow-specific system prompt."""
    return config.SYSTEM_PROMPT


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
    """Get citations for query from vector store."""
    global citation_extractor
    
    if not citation_extractor:
        return None
    
    citations = citation_extractor.extract_from_query(query)
    return citations if citations else None


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

