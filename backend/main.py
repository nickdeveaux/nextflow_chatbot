from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict
from contextlib import asynccontextmanager
import os
import openai
from datetime import datetime
import uuid
import time

# Vector store imports
from vector_store.embeddings import EmbeddingGenerator
from vector_store.faiss_store import FAISSVectorStore
from vector_store.document_loader import prepare_documents_for_indexing

# Global vector store instance
vector_store_instance: Optional[FAISSVectorStore] = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize vector store on startup."""
    global vector_store_instance
    
    print("Initializing vector store...")
    try:
        # Use sentence-transformers (free, offline)
        embedding_gen = EmbeddingGenerator(use_openai=False)
        
        # Get docs directory from env or use default
        docs_dir = os.getenv("NEXTFLOW_DOCS_DIR", "/Users/nickmarveaux/Dev/nextflow/docs")
        index_path = os.getenv("VECTOR_INDEX_PATH", "./vector_index.index")
        
        # Create vector store
        vector_store_instance = FAISSVectorStore(embedding_gen, index_path=index_path)
        
        # Build or load index
        if os.path.exists(index_path) and os.path.exists(index_path.replace('.index', '.data')):
            print("Loading existing vector store index...")
            vector_store_instance.load(index_path)
        else:
            print("Building vector store index from documentation...")
            texts, metadata = prepare_documents_for_indexing(docs_dir=docs_dir)
            if texts:
                vector_store_instance.build_index(texts, metadata)
                print(f"Vector store initialized with {len(texts)} chunks")
            else:
                print("Warning: No documents loaded. Vector store will be empty.")
        
        print("Vector store ready!")
    except Exception as e:
        print(f"Error initializing vector store: {e}")
        print("Falling back to dictionary-based knowledge base")
        vector_store_instance = None
    
    yield
    
    # Cleanup on shutdown (if needed)
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

# Nextflow knowledge base (minimal for demo)
NEXTFLOW_KNOWLEDGE = {
    "version": {
        "latest": "23.10.0",
        "info": "The latest stable version of Nextflow is 23.10.0 (as of 2024). Check https://github.com/nextflow-io/nextflow/releases for the most current version."
    },
    "dsl2": {
        "syntax": {
            "from": "Yes, 'from' is part of DSL2 syntax. It's used in process definitions to define input channels.",
            "into": "Yes, 'into' is part of DSL2 syntax. It's used with operators like 'splitCsv', 'splitFasta', etc., and also with Channel.into() to create multiple output channels."
        },
        "operators": [
            "from", "into", "map", "flatMap", "filter", "groupTuple", "separate", "transpose",
            "splitCsv", "splitFasta", "splitJson", "splitText", "splitFasta", "combine", "join"
        ]
    },
    "executors": {
        "moab": "Yes, Nextflow supports Moab as an executor. It's configured via process.executor = 'moab' in your nextflow.config or process block. Moab is a job scheduler used in HPC environments.",
        "supported": ["local", "sge", "slurm", "pbs", "lsf", "moab", "condor", "nqsii", "ignite", "k8s", "awsbatch", "google-lifesciences", "azure-batch"]
    },
    "troubleshooting": {
        "dsl1_dsl2": {
            "issue": "DSL1 vs DSL2 operator confusion",
            "solution": "DSL2 uses operators like 'from', 'into', 'map', etc. on channels. In DSL1, operators were different. Ensure you're using DSL2 syntax: add 'nextflow.enable.dsl=2' at the top of your script or use 'nextflow run -dsl2'."
        },
        "executor_config": {
            "issue": "Executor configuration",
            "solution": "Set process.executor in nextflow.config or in a process block. For batch schedulers, also configure clusterOptions, queue, etc. Example: process.executor = 'slurm'; process.queue = 'normal'."
        },
        "version_check": {
            "issue": "Version checking",
            "solution": "Check Nextflow version with 'nextflow -v'. Pin a version in your pipeline by specifying it in nextflow.config: 'process.container = 'nextflow/nextflow:23.10.0'' or use conda/mamba environment."
        }
    }
}

def get_knowledge_context(query: str) -> str:
    """Retrieve relevant knowledge using vector store or fallback to dictionary."""
    global vector_store_instance
    
    # Use vector store if available
    if vector_store_instance is not None:
        try:
            # Search for top 3-5 most similar documents
            results = vector_store_instance.search(query, top_k=5, threshold=0.5)
            
            if results:
                context_parts = []
                seen_urls = set()
                
                for text, similarity, metadata in results:
                    # Add document text
                    context_parts.append(text)
                    
                    # Add URL if available and not already added
                    url = metadata.get('url')
                    if url and url not in seen_urls:
                        context_parts.append(f"Source: {url}")
                        seen_urls.add(url)
                
                return "\n\n".join(context_parts)
        except Exception as e:
            print(f"Error in vector store search: {e}")
            # Fall back to dictionary-based lookup
    
    # Fallback to dictionary-based knowledge (for backward compatibility)
    query_lower = query.lower()
    context_parts = []
    
    # Version queries
    if "version" in query_lower or "latest" in query_lower:
        context_parts.append(f"Version info: {NEXTFLOW_KNOWLEDGE['version']['info']}")
    
    # DSL2 syntax queries
    if "dsl2" in query_lower or "dsl 2" in query_lower or "from" in query_lower or "into" in query_lower:
        if "from" in query_lower:
            context_parts.append(NEXTFLOW_KNOWLEDGE['dsl2']['syntax']['from'])
        if "into" in query_lower:
            context_parts.append(NEXTFLOW_KNOWLEDGE['dsl2']['syntax']['into'])
    
    # Executor queries
    if "executor" in query_lower or "moab" in query_lower or "scheduler" in query_lower:
        if "moab" in query_lower:
            context_parts.append(NEXTFLOW_KNOWLEDGE['executors']['moab'])
        context_parts.append(f"Supported executors: {', '.join(NEXTFLOW_KNOWLEDGE['executors']['supported'])}")
    
    # Troubleshooting detection
    if "dsl1" in query_lower or "dsl 1" in query_lower:
        context_parts.append(f"Troubleshooting: {NEXTFLOW_KNOWLEDGE['troubleshooting']['dsl1_dsl2']['solution']}")
    
    if "how to check" in query_lower or "version check" in query_lower or "pin version" in query_lower:
        context_parts.append(f"Troubleshooting: {NEXTFLOW_KNOWLEDGE['troubleshooting']['version_check']['solution']}")
    
    return "\n".join(context_parts) if context_parts else ""

def detect_troubleshooting_need(query: str) -> Optional[str]:
    """Detect if the query is a troubleshooting question."""
    query_lower = query.lower()
    
    if "dsl1" in query_lower or "dsl 1" in query_lower or "dsl2" in query_lower or "dsl 2" in query_lower:
        if "confus" in query_lower or "difference" in query_lower or "operator" in query_lower:
            return NEXTFLOW_KNOWLEDGE['troubleshooting']['dsl1_dsl2']['solution']
    
    if "executor" in query_lower and ("config" in query_lower or "set" in query_lower or "where" in query_lower):
        return NEXTFLOW_KNOWLEDGE['troubleshooting']['executor_config']['solution']
    
    if "version" in query_lower and ("check" in query_lower or "pin" in query_lower or "how" in query_lower):
        return NEXTFLOW_KNOWLEDGE['troubleshooting']['version_check']['solution']
    
    return None

async def get_llm_response(messages: List[Dict], context: str) -> str:
    """Get response from LLM with context."""
    api_key = os.getenv("OPENAI_API_KEY")
    use_mock = os.getenv("USE_MOCK_MODE", "false").lower() == "true"
    
    if use_mock or not api_key:
        # Mock mode - return a helpful response based on context
        time.sleep(10)
        return generate_mock_response(messages[-1]["content"], context)
    
    try:
        client = openai.OpenAI(api_key=api_key)
        
        # Build system prompt
        system_prompt = """You are a helpful Nextflow documentation assistant. You answer questions about Nextflow with accuracy and clarity.
        
Focus on:
- 70% documentation Q&A about Nextflow features, syntax, and capabilities
- 30% pragmatic troubleshooting guidance

When you have relevant context, use it. When something is unknown, be transparent and suggest how to verify it (e.g., check the docs at https://www.nextflow.io/docs/latest/).

Keep responses concise but informative. If asked for citations, provide them."""
        
        # Add context to the last user message if available
        user_message = messages[-1]["content"]
        if context:
            user_message = f"Context: {context}\n\nUser question: {user_message}"
        
        response = client.chat.completions.create(
            model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
            messages=[
                {"role": "system", "content": system_prompt},
                *messages[:-1],  # Previous conversation
                {"role": "user", "content": user_message}
            ],
            temperature=0.7,
            max_tokens=500
        )
        
        return response.choices[0].message.content
    except Exception as e:
        # Fallback to mock mode on error
        return generate_mock_response(messages[-1]["content"], context)

def generate_mock_response(query: str, context: str) -> str:
    """Generate a mock response when API is unavailable."""
    query_lower = query.lower()
    
    # Version query
    if "version" in query_lower:
        if "again" in query_lower or "what was" in query_lower:
            return f"The latest version of Nextflow is {NEXTFLOW_KNOWLEDGE['version']['latest']}. You can check the latest releases at https://github.com/nextflow-io/nextflow/releases"
        return f"The latest version of Nextflow is {NEXTFLOW_KNOWLEDGE['version']['latest']}. Check https://github.com/nextflow-io/nextflow/releases for the most current version."
    
    # DSL2 syntax
    if ("from" in query_lower or "into" in query_lower) or "dsl2" in query_lower:
        if "from" in query_lower and "into" in query_lower:
            return "Yes, both 'from' and 'into' are part of DSL2 syntax. 'from' is used in process definitions to define input channels, and 'into' is used with operators like splitCsv, splitFasta, etc., and also with Channel.into() to create multiple output channels."
        if "from" in query_lower:
            return "Yes, 'from' is part of DSL2 syntax. It's used in process definitions to define input channels. Example: process foo { input: val x from channel1 }"
        if "into" in query_lower:
            return "Yes, 'into' is part of DSL2 syntax. It's used with operators like splitCsv, splitFasta, etc., and also with Channel.into() to create multiple output channels. Example: channel.fromList([1,2,3]).into{ ch1; ch2 }"
    
    # Moab executor
    if "moab" in query_lower:
        return "Yes, Nextflow supports Moab as an executor. Configure it via process.executor = 'moab' in your nextflow.config or process block. Moab is a job scheduler commonly used in HPC environments."
    
    # Citations
    if "cite" in query_lower or "citation" in query_lower or "source" in query_lower:
        return "You can find official Nextflow documentation at https://www.nextflow.io/docs/latest/. For specific topics, check the DSL2 guide: https://www.nextflow.io/docs/latest/dsl2.html"
    
    # Use context if available
    if context:
        troubleshooting = detect_troubleshooting_need(query)
        if troubleshooting:
            return f"{context}\n\nTroubleshooting tip: {troubleshooting}"
        return context
    
    # Default response
    return "I can help you with Nextflow documentation questions. Try asking about versions, DSL2 syntax, executors, or troubleshooting. For official documentation, visit https://www.nextflow.io/docs/latest/"

@app.post("/chat", response_model=ChatResponse)
async def chat(message: ChatMessage):
    """Main chat endpoint."""
    try:
        # Get or create session
        session_id = message.session_id or str(uuid.uuid4())
        if session_id not in sessions:
            sessions[session_id] = []
        
        # Add user message to session
        sessions[session_id].append({
            "role": "user",
            "content": message.message,
            "timestamp": datetime.now().isoformat()
        })
        
        # Get knowledge context
        context = get_knowledge_context(message.message)
        
        # Get LLM response
        reply = await get_llm_response(sessions[session_id], context)
        
        # Add assistant response to session
        sessions[session_id].append({
            "role": "assistant",
            "content": reply,
            "timestamp": datetime.now().isoformat()
        })
        
        # Generate citations from vector store results if available
        citations = None
        if "cite" in message.message.lower() or "citation" in message.message.lower():
            citations = []
            if vector_store_instance is not None:
                try:
                    results = vector_store_instance.search(message.message, top_k=3, threshold=0.5)
                    seen_urls = set()
                    for _, _, metadata in results:
                        url = metadata.get('url')
                        if url and url not in seen_urls:
                            citations.append(url)
                            seen_urls.add(url)
                except Exception:
                    pass
            
            # Fallback to default citations
            if not citations:
                citations = [
                    "https://www.nextflow.io/docs/latest/",
                    "https://www.nextflow.io/docs/latest/dsl2.html",
                    "https://github.com/nextflow-io/nextflow"
                ]
        
        return ChatResponse(
            reply=reply,
            session_id=session_id,
            citations=citations
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing chat: {str(e)}")

@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "ok"}

