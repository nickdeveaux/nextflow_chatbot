"""
Example implementation showing how to integrate vector store into main.py
This is a reference implementation - integrate into main.py as needed.
"""
import os
from vector_store.embeddings import EmbeddingGenerator
from vector_store.faiss_store import FAISSVectorStore
from vector_store.document_loader import prepare_documents_for_indexing

# Initialize vector store (do this once at startup)
def initialize_vector_store():
    """Initialize and load vector store."""
    # Create embedding generator
    embedding_gen = EmbeddingGenerator()
    
    # Create vector store
    index_path = os.getenv("VECTOR_INDEX_PATH", "./vector_index.index")
    vector_store = FAISSVectorStore(embedding_gen, index_path=index_path)
    
    # Build index if it doesn't exist
    if not os.path.exists(index_path):
        print("Building vector store index...")
        texts, metadata = prepare_documents_for_indexing()
        vector_store.build_index(texts, metadata)
    else:
        print("Loading existing vector store index...")
        vector_store.load(index_path)
    
    return vector_store


# Example usage in get_knowledge_context replacement
def get_knowledge_context_vector(query: str, vector_store: FAISSVectorStore) -> str:
    """
    Retrieve relevant knowledge using vector similarity search.
    Replaces the old get_knowledge_context() function.
    """
    # Search for top 3 most similar documents
    results = vector_store.search(query, top_k=3, threshold=0.5)
    
    if not results:
        return ""
    
    # Combine results into context
    context_parts = []
    for text, similarity, metadata in results:
        context_parts.append(f"[Similarity: {similarity:.2f}] {text}")
        if metadata.get('url'):
            context_parts.append(f"Source: {metadata['url']}")
    
    return "\n\n".join(context_parts)


# In main.py, you would:
# 1. Initialize vector store at startup (outside FastAPI app or in startup event)
# 2. Replace get_knowledge_context() calls with get_knowledge_context_vector()
# 3. Store vector_store instance globally or in app state

# Example FastAPI integration:
"""
from contextlib import asynccontextmanager

vector_store_instance = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    global vector_store_instance
    vector_store_instance = initialize_vector_store()
    yield
    # Shutdown (cleanup if needed)

app = FastAPI(lifespan=lifespan)

@app.post("/chat")
async def chat(message: ChatMessage):
    # Use vector_store_instance instead of get_knowledge_context()
    context = get_knowledge_context_vector(message.message, vector_store_instance)
    # ... rest of the function
"""

