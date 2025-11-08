# Vector Store

## Overview

Semantic search over Nextflow documentation using embeddings and cosine similarity.

## Components

- **Embeddings**: `sentence-transformers/all-MiniLM-L6-v2` (384-dim vectors)
- **Vector Store**: FAISS (fast similarity search)
- **Document Processing**: Loads markdown files, chunks into 200-500 token segments

## Flow

```
User Query → Embed Query → Search FAISS → Get Top-K Results → Format Context → Send to LLM
```

## Implementation

- **Embedding Model**: Sentence Transformers (CPU-optimized, single-threaded)
- **Storage**: FAISS index persisted to disk (`/app/data/vector_index.index`)
- **Index Building**: Auto-built on first startup from Nextflow docs (cloned during Docker build)

## Configuration

- `VECTOR_INDEX_PATH` - Index file path (default: `/app/data/vector_index.index`)
- `NEXTFLOW_DOCS_DIR` - Docs directory (default: `/app/nextflow-docs`, auto-cloned)
- `VECTOR_SEARCH_TOP_K` - Number of results (default: `5`)
- `VECTOR_SEARCH_THRESHOLD` - Minimum similarity score (default: `0.4`)

