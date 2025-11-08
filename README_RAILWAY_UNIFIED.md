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

In Railway dashboard, go to your service → **Variables** and add:

#### Required Variables

```bash
# Google Cloud Service Account (for Vertex AI)
SERVICE_ACCOUNT_PATH=/app/service-account.json

# LLM Configuration
LLM_MODEL=gemini-2.0-flash-exp
LLM_MAX_TOKENS=1000

# Vector Store (optional - for building index at runtime)
VECTOR_INDEX_PATH=/app/data/vector_index.index
NEXTFLOW_DOCS_DIR=/app/nextflow-docs

# Frontend API URL (empty string for relative URLs, since same origin)
NEXT_PUBLIC_API_URL=
```

#### Optional Variables

```bash
# Vector Store Configuration
VECTOR_SEARCH_TOP_K=5
VECTOR_SEARCH_THRESHOLD=0.4

# Nextflow Docs Branch (for building index)
NEXTFLOW_BRANCH=master  # or specific version like v24.04.0

# Build Index at Runtime (set to true to build index during deployment)
BUILD_INDEX=false  # Set to true if you want to build index during build
```

### 3. Add Service Account File

1. In Railway dashboard, go to your service → **Variables**
2. Click **"New Variable"**
3. Select **"File"** type
4. Name: `SERVICE_ACCOUNT_PATH`
5. Upload your Google Cloud service account JSON file
6. Set the path: `/app/service-account.json`

Alternatively, you can:
- Add the service account JSON content as a variable (not recommended for security)
- Use Railway's secrets management

### 4. Configure Build Arguments (Optional)

If you want to build the vector index during Docker build:

1. Go to Railway dashboard → Your service → **Settings**
2. Under **"Build"**, add build arguments:
   - `BUILD_INDEX=true` - Build index during build
   - `NEXTFLOW_BRANCH=master` - Nextflow docs branch/tag

**Note**: Building the index during build increases build time significantly. It's recommended to:
- Pre-build the index and commit it to the repo, OR
- Build the index on first startup (set `BUILD_INDEX=false` and provide `NEXTFLOW_DOCS_DIR`)

### 5. Deploy

1. **Push your code** to GitHub (Railway will auto-deploy)
2. Or trigger a manual deployment in Railway dashboard
3. **Monitor the logs** to ensure both services start correctly

### 6. Verify Deployment

Once deployed, Railway will provide a URL like: `https://your-app.railway.app`

Test the deployment:
1. **Frontend**: Visit `https://your-app.railway.app` - should show the chat interface
2. **Backend Health**: Visit `https://your-app.railway.app/health` - should return `{"status": "ok"}`
3. **Chat API**: The frontend should be able to communicate with the backend

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

### Backend Not Starting

1. Check Railway logs for errors
2. Verify `SERVICE_ACCOUNT_PATH` is set correctly
3. Check that service account file is uploaded
4. Verify environment variables are set

### Frontend Not Loading

1. Check Railway logs for Next.js errors
2. Verify `NEXT_PUBLIC_API_URL` is set (can be relative `/`)
3. Check that frontend build completed successfully

### Vector Store Issues

1. If index doesn't exist:
   - Set `BUILD_INDEX=true` to build during deployment
   - Or provide pre-built index files in the repo
   - Or set `NEXTFLOW_DOCS_DIR` to build on first startup

2. If index build fails:
   - Check `NEXTFLOW_DOCS_DIR` is set correctly
   - Verify `NEXTFLOW_BRANCH` is valid
   - Check build logs for errors

### Port Issues

- Railway automatically sets the `PORT` environment variable
- The reverse proxy listens on this port
- Internal services (FastAPI: 8001, Next.js: 3000) are not exposed externally

## Environment Variables Reference

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `SERVICE_ACCOUNT_PATH` | Yes | - | Path to Google Cloud service account JSON |
| `LLM_MODEL` | No | `gemini-2.0-flash-exp` | Gemini model to use |
| `LLM_MAX_TOKENS` | No | `1000` | Maximum output tokens |
| `VECTOR_INDEX_PATH` | No | `/app/data/vector_index.index` | Path to vector index |
| `NEXTFLOW_DOCS_DIR` | No | - | Path to Nextflow docs (for building index) |
| `NEXT_PUBLIC_API_URL` | No | `http://localhost:8000` | Frontend API URL (set to empty string `""` for relative URLs on same origin) |
| `BUILD_INDEX` | No | `false` | Build index during Docker build |
| `NEXTFLOW_BRANCH` | No | `master` | Nextflow docs branch/tag |

## Advantages of Unified Deployment

✅ **Single service** - Easier to manage and monitor  
✅ **Single port** - No CORS issues, simpler configuration  
✅ **Cost effective** - One Railway service instead of two  
✅ **Simplified deployment** - One Dockerfile, one service  
✅ **Same origin** - Frontend and backend on same domain  

## Disadvantages

⚠️ **Single point of failure** - If one service crashes, both are affected  
⚠️ **Resource sharing** - Frontend and backend share the same container resources  
⚠️ **Scaling** - Cannot scale frontend and backend independently  

For production with high traffic, consider deploying frontend and backend separately.

## Local Development

For local development, continue using the separate services:

```bash
# Backend
cd backend
uvicorn main:app --host 0.0.0.0 --port 8000

# Frontend (separate terminal)
cd frontend
npm run dev
```

The unified Dockerfile is only for Railway deployment.

### Testing the Unified Dockerfile Locally

You can test the unified Dockerfile locally before deploying to Railway:

```bash
# Build the image
docker build -f Dockerfile.railway -t nextflow-chatbot-unified .

# Run the container
docker run -p 8000:8000 \
  -e SERVICE_ACCOUNT_PATH=/app/service-account.json \
  -v /path/to/service-account.json:/app/service-account.json:ro \
  -e NEXT_PUBLIC_API_URL= \
  nextflow-chatbot-unified

# Test the deployment
curl http://localhost:8000/health
# Open http://localhost:8000 in your browser
```

## Updating the Deployment

1. **Push changes** to GitHub
2. Railway will **automatically rebuild and redeploy**
3. Monitor the **deployment logs** for errors
4. Test the **deployed URL** after deployment completes

## Support

For issues or questions:
1. Check Railway logs for errors
2. Verify environment variables are set correctly
3. Check that all required files are present
4. Review the troubleshooting section above

