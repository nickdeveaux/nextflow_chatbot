from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict
from contextlib import asynccontextmanager
import os
from datetime import datetime
import uuid
from litellm import completion

from vector_store.embeddings import EmbeddingGenerator
from vector_store.faiss_store import FAISSVectorStore
from vector_store.document_loader import prepare_documents_for_indexing
from citations import CitationExtractor

vector_store_instance: Optional[FAISSVectorStore] = None
citation_extractor: Optional[CitationExtractor] = None

def _initialize_vector_store():
    """Initialize vector store instance."""
    global vector_store_instance
    embedding_gen = EmbeddingGenerator(use_openai=False)
    docs_dir = os.getenv("NEXTFLOW_DOCS_DIR", "/Users/nickmarveaux/Dev/nextflow/docs")
    index_path = os.getenv("VECTOR_INDEX_PATH", "./vector_index.index")
    return FAISSVectorStore(embedding_gen, index_path=index_path)


def _load_or_build_index(vector_store: FAISSVectorStore):
    """Load existing index or build new one."""
    index_path = os.getenv("VECTOR_INDEX_PATH", "./vector_index.index")
    data_path = index_path.replace('.index', '.data')
    
    if os.path.exists(index_path) and os.path.exists(data_path):
        print("Loading existing vector store index...")
        vector_store.load(index_path)
    else:
        print("Building vector store index from documentation...")
        docs_dir = os.getenv("NEXTFLOW_DOCS_DIR", "/Users/nickmarveaux/Dev/nextflow/docs")
        texts, metadata = prepare_documents_for_indexing(docs_dir=docs_dir)
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
    
    for text, _, metadata in results:
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
        results = vector_store_instance.search(query, top_k=5, threshold=0.5)
        return _format_context(results) if results else ""
    except Exception as e:
        print(f"Error in vector store search: {e}")
        return ""

def _get_system_prompt() -> str:
    """Get Nextflow-specific system prompt."""
    return """You are a helpful Nextflow documentation assistant. You answer questions about Nextflow with accuracy and clarity.

Nextflow is a workflow management system for data-intensive computational pipelines. It enables scalable and reproducible scientific workflows using a simple DSL (Domain-Specific Language).

Focus on:
- 70% documentation Q&A about Nextflow features, syntax, and capabilities
- 30% pragmatic troubleshooting guidance

When you have relevant context from documentation, use it. When something is unknown, be transparent and suggest how to verify it (e.g., check the docs at https://www.nextflow.io/docs/latest/).

Keep responses concise but informative. If asked for citations, provide them."""


def _build_messages(conversation_history: List[Dict], query: str, context: str) -> List[Dict]:
    """Build message list for LLM."""
    messages = []
    if conversation_history:
        for msg in conversation_history[:-1]:
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
    """Call Gemini 2.5 directly via Vertex API."""
    api_key = os.getenv(
        "GOOGLE_VERTEX_API_KEY", 
        "REMOVED"
    )
    
    messages = _build_messages(conversation_history or [], query, context)
    
    try:
        response = completion(
            model="vertex_ai/gemini-2.0-flash-exp",
            messages=messages,
            api_key=api_key,
            temperature=0.7,
            max_tokens=500
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"Error calling Gemini: {e}")
        raise

async def get_llm_response(messages: List[Dict], context: str) -> str:
    """Get response from LLM with context."""
    query = messages[-1]["content"]
    
    try:
        return await call_gemini_direct(query, messages, context)
    except Exception as e:
        print(f"Error in get_llm_response: {e}")
        try:
            return await call_gemini_direct(query, messages, "")
        except Exception as e2:
            raise HTTPException(
                status_code=500, 
                detail=f"LLM service unavailable: {str(e2)}"
            )

def _get_or_create_session(session_id: Optional[str]) -> str:
    """Get existing session or create new one."""
    if not session_id:
        return str(uuid.uuid4())
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
        session_id = _get_or_create_session(message.session_id)
        _add_user_message(session_id, message.message)
        
        context = get_knowledge_context(message.message)
        reply = await get_llm_response(sessions[session_id], context)
        
        _add_assistant_message(session_id, reply)
        citations = _get_citations(message.message)
        
        return ChatResponse(
            reply=reply,
            session_id=session_id,
            citations=citations
        )
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"Error processing chat: {str(e)}"
        )

@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "ok"}

