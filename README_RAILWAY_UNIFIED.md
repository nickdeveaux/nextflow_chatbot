# Railway Unified Deployment Guide

This guide explains how to deploy the Nextflow Chat Assistant as a **single unified service** on Railway, where both frontend and backend run in one container.

## Overview

The unified deployment uses:
- **Next.js standalone server** - Serves the frontend on port 3000 (internal)
- **FastAPI backend** - Serves the API on port 8001 (internal)
- **Reverse proxy** - Routes requests on Railway's port (8000):
  - `/chat`, `/health` → FastAPI backend
  - Everything else → Next.js frontend

This approach allows Railway to run everything in a single container while maintaining separation of concerns.

## Prerequisites

1. A Railway account
2. Your Google Cloud service account JSON file
3. Git repository with your code

## Deployment Steps

### 1. Configure Railway Service

1. **Create a new Railway project** (or use an existing one)
2. **Add a new service**:
   - Click "New" → "GitHub Repo" (select your repository)
   - Or use Railway CLI: `railway init`

3. **Configure the service**:
   - Set **Root Directory**: Leave empty (project root)
   - Set **Dockerfile Path**: `Dockerfile.railway`
   - Railway will automatically detect and use the Dockerfile

### 2. Set Environment Variables

In Railway dashboard → **Variables**, add:

**Required:**
- `SERVICE_ACCOUNT_PATH=/app/service-account.json` - Upload your Google Cloud service account JSON file as a **File** variable
- `NEXT_PUBLIC_API_URL=` - Empty string for relative URLs (same origin)

**Optional:**
- `LLM_MODEL=gemini-2.0-flash-exp` - Gemini model
- `LLM_MAX_TOKENS=1000` - Max output tokens
- `VECTOR_INDEX_PATH=/app/data/vector_index.index` - Vector index path
- `BUILD_INDEX=false` - Build index during build (set to `true` to build during deployment)
- `NEXTFLOW_BRANCH=master` - Nextflow docs branch/tag

### 3. Configure Build Arguments (Optional)

If you want to build the vector index during Docker build:

1. Go to Railway dashboard → Your service → **Settings**
2. Under **"Build"**, add build arguments:
   - `BUILD_INDEX=true` - Build index during build
   - `NEXTFLOW_BRANCH=master` - Nextflow docs branch/tag

**Note**: Building the index during build increases build time. Recommended: pre-build the index and commit it to the repo.

### 4. Deploy

1. **Push your code** to GitHub (Railway will auto-deploy)
2. **Monitor the logs** to ensure both services start correctly
3. **Test the deployment**:
   - Frontend: Visit your Railway URL (should show chat interface)
   - Health: `https://your-app.railway.app/health` (should return `{"status": "ok"}`)

## Architecture

```
Railway Port (8000)
    │
    ├─ Reverse Proxy (proxy.js)
    │     │
    │     ├─ /chat, /health → FastAPI (port 8001)
    │     └─ /* → Next.js (port 3000)
    │
    ├─ FastAPI Backend (port 8001)
    │     ├─ /chat - Chat endpoint
    │     ├─ /health - Health check
    │     └─ Vector store & LLM client
    │
    └─ Next.js Frontend (port 3000)
          ├─ Static assets
          ├─ React app
          └─ Client-side routing
```

## Troubleshooting

### Common Issues

**Backend not starting:**
- Check Railway logs for errors
- Verify `SERVICE_ACCOUNT_PATH` is set and file is uploaded
- Verify environment variables are set correctly

**Frontend not loading:**
- Check Railway logs for Next.js errors
- Verify `NEXT_PUBLIC_API_URL` is set (empty string for relative URLs)
- Check that frontend build completed successfully

**Vector store issues:**
- Index doesn't exist: Set `BUILD_INDEX=true` or provide pre-built index files
- Index build fails: Check `NEXTFLOW_DOCS_DIR` and `NEXTFLOW_BRANCH` are valid

## Advantages & Limitations

**Advantages:**
- Single service deployment (easier to manage, cost-effective)
- No CORS issues (same origin)
- Simplified configuration

**Limitations:**
- Single point of failure (services share container)
- Cannot scale frontend and backend independently
- Resource sharing between services

For high-traffic production, consider deploying frontend and backend separately.

## Testing Locally

Test the unified Dockerfile before deploying to Railway:

```bash
# Build the image
docker build -f Dockerfile.railway -t nextflow-chatbot-unified .

# Run the container
docker run -p 8000:8000 \
  -e SERVICE_ACCOUNT_PATH=/app/service-account.json \
  -v /path/to/service-account.json:/app/service-account.json:ro \
  -e NEXT_PUBLIC_API_URL= \
  nextflow-chatbot-unified

curl http://localhost:8000/health
# Open http://localhost:8000 in your browser
```

**Note:** For local development, continue using separate services (backend on port 8000, frontend on port 3000). The unified Dockerfile is only for Railway deployment.

