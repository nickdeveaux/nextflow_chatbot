# Railway Unified Deployment - Quick Summary

This document provides a quick reference for deploying the Nextflow Chat Assistant as a **single unified service** on Railway.

## Quick Start

1. **Create Railway service** with `Dockerfile.railway`
2. **Set environment variables**:
   - `SERVICE_ACCOUNT_PATH=/app/service-account.json` (upload your service account file)
   - `NEXT_PUBLIC_API_URL=` (empty string for relative URLs)
3. **Deploy** - Railway will automatically build and deploy

## How It Works

```
┌─────────────────────────────────────────┐
│  Railway Port (8000)                    │
│  ┌───────────────────────────────────┐  │
│  │  Reverse Proxy (proxy.js)         │  │
│  │  • /chat, /health → FastAPI       │  │
│  │  • /* → Next.js                   │  │
│  └───────────────────────────────────┘  │
│           │                    │         │
│     ┌─────┴─────┐       ┌──────┴──────┐ │
│     │ FastAPI   │       │  Next.js    │ │
│     │ :8001     │       │  :3000      │ │
│     └───────────┘       └─────────────┘ │
└─────────────────────────────────────────┘
```

## Key Files

- **`Dockerfile.railway`** - Unified Dockerfile for Railway
- **`railway-unified.json`** - Railway configuration
- **`README_RAILWAY_UNIFIED.md`** - Full deployment guide

## Environment Variables

### Required
- `SERVICE_ACCOUNT_PATH` - Path to Google Cloud service account JSON

### Recommended
- `NEXT_PUBLIC_API_URL=` - Empty string for relative URLs (same origin)

### Optional
- `LLM_MODEL` - Gemini model (default: `gemini-2.0-flash-exp`)
- `LLM_MAX_TOKENS` - Max output tokens (default: `1000`)
- `BUILD_INDEX` - Build vector index during build (default: `false`)
- `NEXTFLOW_BRANCH` - Nextflow docs branch (default: `master`)

## Testing Locally

```bash
docker build -f Dockerfile.railway -t nextflow-chatbot-unified .
docker run -p 8000:8000 \
  -e SERVICE_ACCOUNT_PATH=/app/service-account.json \
  -v /path/to/service-account.json:/app/service-account.json:ro \
  -e NEXT_PUBLIC_API_URL= \
  nextflow-chatbot-unified
```

## Advantages

✅ Single service deployment  
✅ No CORS issues (same origin)  
✅ Simplified configuration  
✅ Cost effective  

## Notes

- Frontend and backend run in the same container
- Reverse proxy routes requests to the appropriate service
- All services share the same container resources
- Cannot scale frontend and backend independently

For full documentation, see [README_RAILWAY_UNIFIED.md](./README_RAILWAY_UNIFIED.md).

