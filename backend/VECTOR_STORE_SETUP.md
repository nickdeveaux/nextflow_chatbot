# Vector Store Setup

The application uses a vector store with FAISS and sentence-transformers for semantic search over Nextflow documentation.

## How It Works

1. **On first startup**: 
   - Loads all markdown files from `/Users/nickmarveaux/Dev/nextflow/docs`
   - Chunks documents into ~400 token pieces
   - Generates embeddings using sentence-transformers (offline, free)
   - Builds FAISS index for fast similarity search
   - Saves index to disk (`vector_index.index` and `vector_index.data`)

2. **On subsequent starts**:
   - Loads existing index from disk (much faster)

3. **During queries**:
   - User query is embedded
   - Cosine similarity search finds top-k most relevant chunks
   - Retrieved chunks are sent as context to the LLM

## Configuration

Set these environment variables:

- `NEXTFLOW_DOCS_DIR`: Path to Nextflow docs directory (default: `/Users/nickmarveaux/Dev/nextflow/docs`)
- `VECTOR_INDEX_PATH`: Where to save/load the index (default: `./vector_index.index`)

## Benefits

- **Free**: No API costs (uses sentence-transformers)
- **Offline**: Works without internet connection
- **Fast**: FAISS provides millisecond similarity search
- **Semantic**: Finds relevant docs even without exact keyword matches
- **Scalable**: Easy to add more documentation

## Troubleshooting

### Index not building

- Check that `NEXTFLOW_DOCS_DIR` points to the correct directory
- Verify markdown files exist in that directory
- Check logs for errors during initialization

### Slow first startup

- First build takes 5-10 minutes (embedding generation)
- Subsequent starts are fast (loads from disk)

### Out of memory

- Reduce chunk size in `document_loader.py`
- Use fewer documents (filter in `load_docs_from_directory`)

## Rebuilding the Index

To rebuild the index (e.g., after updating docs):

1. Delete `vector_index.index` and `vector_index.data`
2. Restart the backend
3. It will rebuild automatically

