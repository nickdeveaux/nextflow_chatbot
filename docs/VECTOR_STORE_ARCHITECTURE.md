# Vector Store Architecture for Nextflow Chatbot

## Overview

This document proposes an architecture for replacing the dictionary-based knowledge base with a vector store that uses cosine similarity for semantic search.

## Architecture Components

### 1. **Embedding Generation**
- **Purpose**: Convert text (queries and documents) into dense vector representations
- **Implementation**: **Sentence Transformers** (`sentence-transformers/all-MiniLM-L6-v2`)
  - Pros: Free, offline, fast, good quality
  - Cons: Slightly lower quality than paid services (but sufficient for this use case)

### 2. **Vector Store**
- **Purpose**: Store document embeddings and enable fast similarity search
- **Options**:
  - **FAISS** (Facebook AI Similarity Search)
    - Pros: Fast, in-memory or disk-based, no external service
    - Cons: In-memory loses data on restart (unless persisted)
  - **Chroma** (local or hosted)
    - Pros: Easy to use, persistent storage, good for small to medium datasets
    - Cons: Less scalable than dedicated services
  - **Qdrant** (self-hosted or cloud)
    - Pros: Production-ready, scalable, supports filtering
    - Cons: Requires deployment/management
  - **Pinecone** (managed service)
    - Pros: Fully managed, scalable, good for production
    - Cons: Costs money, external dependency
  - **Simple in-memory with NumPy**
    - Pros: No dependencies, simple for demo
    - Cons: Not scalable, loses data on restart

### 3. **Document Chunking**
- Split Nextflow documentation into chunks (e.g., 200-500 tokens)
- Store chunks with metadata (source URL, section, topic)
- Each chunk becomes a vector in the store

### 4. **Retrieval Flow**

```
User Query
    ↓
Generate Query Embedding
    ↓
Cosine Similarity Search (top-k results)
    ↓
Retrieve Document Chunks + Metadata
    ↓
Combine into Context
    ↓
Send to LLM with Context
```

## Proposed Implementation (Simple & Production-Ready)

### Option A: FAISS + Sentence Transformers (Recommended for Demo)

**Why**: Free, offline, fast, good for interviews

```python
# Components:
1. sentence-transformers for embeddings
2. FAISS for vector storage
3. Persist index to disk for startup
```

**Pros**:
- No API costs
- Works offline
- Fast similarity search
- Can persist to disk

**Cons**:
- Requires embedding model download (~80MB)

### Option C: Chroma (Local)

**Why**: Persistent, easy to use, good for production demos

**Pros**:
- Built-in persistence
- Easy to add/remove documents
- Good for small to medium datasets

**Cons**:
- Slightly slower than FAISS for large datasets

## Implementation Structure

```
backend/
├── vector_store/
│   ├── __init__.py
│   ├── embeddings.py          # Embedding generation
│   ├── store.py               # Vector store interface
│   ├── faiss_store.py         # FAISS implementation
│   └── document_loader.py     # Load/preprocess documents
├── knowledge/
│   └── documents/             # Nextflow docs (markdown/text)
└── main.py                    # Updated to use vector store
```

## Data Flow

1. **Initialization** (on startup):
   - Load documents from `knowledge/documents/`
   - Chunk documents (e.g., 300 tokens each)
   - Generate embeddings for each chunk
   - Build FAISS index
   - Persist index to disk

2. **Query Time**:
   - User sends query
   - Generate embedding for query
   - Search FAISS index (top-k, e.g., k=3-5)
   - Retrieve chunks with highest cosine similarity
   - Combine chunks into context
   - Send to LLM

3. **Cosine Similarity**:
   - Formula: `similarity = dot(query_embedding, doc_embedding) / (||query|| * ||doc||)`
   - Returns values between -1 and 1 (closer to 1 = more similar)
   - Threshold: Typically return top-k results above 0.7 similarity

## Example Query Flow

```
Query: "What is the latest version of Nextflow?"

1. Embed query → [0.1, -0.3, 0.5, ...] (1536-dim vector)
2. Search FAISS → Find top 3 chunks:
   - Chunk 1: "Nextflow version 23.10.0..." (similarity: 0.89)
   - Chunk 2: "Version history..." (similarity: 0.82)
   - Chunk 3: "Installation guide..." (similarity: 0.65)
3. Combine chunks → Context string
4. Send to LLM with context
```

## Scaling Considerations

- **Small scale** (< 1000 docs): FAISS in-memory, sentence-transformers
- **Medium scale** (< 10k docs): FAISS on disk, batch embedding
- **Large scale** (> 10k docs): Chroma/Qdrant, async embedding generation
- **Production**: Pinecone or self-hosted Qdrant

## Integration Points

Replace `get_knowledge_context()` function in `main.py`:

```python
# Old:
context = get_knowledge_context(message.message)

# New:
context = vector_store.search(query=message.message, top_k=3)
```

## Benefits Over Dictionary Approach

1. **Semantic understanding**: Finds relevant docs even without exact keyword matches
2. **Scalability**: Easy to add more documents
3. **Flexibility**: Can handle varied question phrasings
4. **Better context**: Retrieves most semantically similar content
5. **Production-ready**: Standard RAG pattern

## Trade-offs

- **Complexity**: More moving parts than simple dict
- **Latency**: Embedding generation adds ~50-200ms
- **Storage**: Embeddings require disk space (but reasonable)
- **Dependencies**: Additional packages needed

