# Deployment Guide

## Production Deployment (Railway)

### Quick Start with Pre-built Index (Recommended)

1. **Commit pre-built index files to repository**:
   ```bash
   git add backend/vector_index.index backend/vector_index.data
   git commit -m "Add pre-built vector index"
   ```

2. **Deploy with minimal dependencies**:
   - Dockerfile automatically detects index files
   - Only installs `requirements.txt` (no torch, no sentence-transformers)
   - Fast deployment, small Docker image

3. **Build Docker image**:
   ```bash
   docker build -t nextflow-chatbot .
   # Or on Railway, just push to GitHub - BUILD_INDEX=false by default
   ```

### Building Index at Runtime

If you need to build the index during deployment:

1. **Build with BUILD_INDEX=true**:
   ```bash
   docker build --build-arg BUILD_INDEX=true -t nextflow-chatbot .
   ```

2. **This will**:
   - Install `requirements-build-index.txt` (torch, sentence-transformers)
   - Clone Nextflow docs
   - Build index from documentation
   - Slower build, larger image

### Check Index Status

Run the check script to see if index exists:
```bash
cd backend
python check_index.py
```

Output:
- `✓ Index files found` - No need for requirements-build-index.txt
- `✗ Index files not found` - Need requirements-build-index.txt if building

## Requirements Files

### `requirements.txt` (Production)
- **Always installed** - minimal dependencies
- FastAPI, uvicorn, google-genai
- faiss-cpu, numpy
- **No torch, no sentence-transformers**
- ~50MB total

### `requirements-build-index.txt` (Index Building)
- **Only installed if BUILD_INDEX=true**
- Includes all of requirements.txt
- Adds: torch (CPU-only), sentence-transformers, transformers
- ~500MB total (only needed for building)

### `requirements-dev.txt` (Development)
- Includes requirements.txt
- Adds: pytest, pytest-asyncio, httpx
- For local development and testing

## How It Works

### Lazy Loading Pattern

The code uses **lazy imports** to avoid loading heavy dependencies:

1. **If index exists** (production):
   - Requires sentence-transformers for query embeddings
   - Install via requirements-build-index.txt if vector search is needed
   - EmbeddingGenerator only imported when needed
   - Fast startup, minimal memory

2. **If index missing** (building):
   - Requires sentence-transformers to build
   - EmbeddingGenerator imported only when building
   - Falls back gracefully if not available

### Index Detection

The `check_index.py` script:
- Checks if `vector_index.index` and `vector_index.data` exist
- Reports file sizes
- Can be used in Dockerfile to determine build strategy
- Helps decide if requirements-build-index.txt is needed

### Smart Defaults

`config.py` automatically determines index path:
- **Container** (`/app` exists): `/app/data/vector_index.index`
- **Local dev**: `./vector_index.index`
- **Custom**: Set via `VECTOR_INDEX_PATH` env var

## Railway Deployment

### Option 1: Pre-built Index (Recommended)

1. Commit index files to repo
2. Push to Railway
3. Railway builds with `BUILD_INDEX=false` (default)
4. Fast deployment, small image

### Option 2: Build at Runtime

1. Set build arg: `BUILD_INDEX=true`
2. Railway installs requirements-build-index.txt
3. Index built from docs during deployment
4. Slower build, but no need to commit large files

## Benefits

✅ **Minimal production dependencies** - No torch in production
✅ **Fast deployments** - Small Docker images
✅ **Flexible** - Build index locally or in container
✅ **Graceful degradation** - Works with or without index
✅ **Cost effective** - No heavy ML libraries in production
