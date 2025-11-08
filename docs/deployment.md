# Deployment Guide

## Backend (Railway)

1. **Create Railway project**: [railway.app](https://railway.app) → New Project → Deploy from GitHub
2. **Auto-detects**: `backend/Dockerfile` and `PORT` environment variable
3. **Set environment variables**:
   ```
   GOOGLE_SERVICE_ACCOUNT_JSON={"type":"service_account",...}  # Required
   LLM_MODEL=gemini-2.0-flash-exp  # Optional
   LLM_MAX_TOKENS=1000  # Optional
   ```
4. **Deploy**: Railway builds and deploys automatically
5. **Copy backend URL**: e.g., `https://your-backend.railway.app`

## Frontend (Vercel)

1. **Create Vercel project**: [vercel.com](https://vercel.com) → New Project → Import GitHub repo
2. **Configure**:
   - **Root Directory**: `frontend`
   - **Framework**: Next.js (auto-detected)
3. **Set environment variable**:
   - `NEXT_PUBLIC_API_URL=https://your-backend.railway.app` (required)
4. **Deploy**: Vercel builds and deploys automatically

## CORS

Backend automatically allows Vercel domains (configured in `config.yaml`). For additional origins, set `CORS_ORIGINS` environment variable or update `config.yaml`.

## Environment Variables

### Backend (Railway)
- `GOOGLE_SERVICE_ACCOUNT_JSON` - Service account JSON (required)
- `SERVICE_ACCOUNT_PATH` - Alternative: file path
- `LLM_MODEL` - Model name (default: `gemini-2.0-flash-exp`)
- `LLM_MAX_TOKENS` - Max output tokens (default: `1000`)
- `LLM_TEMPERATURE` - Temperature (default: `0.7`)
- `VECTOR_INDEX_PATH` - Index path (default: `/app/data/vector_index.index`)
- `CORS_ORIGINS` - Allowed origins (comma-separated, optional)

### Frontend (Vercel)
- `NEXT_PUBLIC_API_URL` - Backend API URL (required)
- `NEXT_PUBLIC_LOADING_MESSAGES` - Loading messages (optional)
- `NEXT_PUBLIC_MAX_INPUT_LENGTH` - Max input length (optional, default: `500000`)
