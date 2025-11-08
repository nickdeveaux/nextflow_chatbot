# Nextflow Chat Assistant

A chat assistant that answers Nextflow documentation questions using semantic search and LLM responses.

## Features

- ✅ **Multi-turn conversations** - Maintains context within sessions
- ✅ **Vector search** - Semantic search over Nextflow documentation with citations
- ✅ **Responsive UI** - Works on desktop and mobile devices (iOS-friendly)
- ✅ **Markdown rendering** - Rich text formatting for code blocks, links, lists
- ✅ **Error handling** - Graceful degradation with clear error messages
- ✅ **Loading states** - Animated loading indicators
- ✅ **Dark mode** - Theme toggle for user preference
- ✅ **Character limit** - Input validation with visual feedback
- ✅ **Security** - Light prompt injection detection

## Tech Stack

- **Frontend**: Next.js 14 with TypeScript, React, Markdown rendering
- **Backend**: FastAPI (Python) with async support
- **LLM**: Google Gemini 2.0 Flash via Vertex AI
- **Vector Store**: FAISS with sentence-transformers for semantic search
- **Deployment**: Railway (backend) + Vercel (frontend) or Railway (full stack)

## Local Setup

### Prerequisites

- **Node.js 18.17 or later** and npm (Next.js 14 requires Node.js 18.17+)
- Python 3.9+

### Backend Setup

1. Navigate to the backend directory:
```bash
cd backend
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set environment variables (optional - defaults are in `config.yaml`):
```bash
# Required for Vertex AI (choose one method):
export GOOGLE_SERVICE_ACCOUNT_JSON='{"type":"service_account",...}'  # Recommended: JSON content
# OR
export SERVICE_ACCOUNT_PATH="path/to/service-account.json"  # File path

# Optional: Vector store configuration
export NEXTFLOW_DOCS_DIR="path/to/nextflow/docs"  # Local docs directory (optional)
export VECTOR_INDEX_PATH="./vector_index.index"  # Local index path (optional)
```

**Note**: 
- Configuration is managed via `config.yaml` (shared between frontend/backend)
- Service account can be provided via `GOOGLE_SERVICE_ACCOUNT_JSON` (env var with JSON) or `SERVICE_ACCOUNT_PATH` (file path)
- Vector store requires Nextflow docs - they're automatically cloned during Docker build, or set `NEXTFLOW_DOCS_DIR` for local dev
- The vector store will automatically build an index from Nextflow docs on first run

5. Run the backend server:
```bash
uvicorn main:app --reload --port 8000
```

The backend will be available at `http://localhost:8000`

### Frontend Setup

1. Navigate to the frontend directory:
```bash
cd frontend
```

2. Install dependencies:
```bash
npm install
```

3. Sync configuration from `config.yaml` (auto-runs on build, but can run manually):
```bash
npm run sync-config
```

4. Set environment variables (optional - defaults in `config.yaml`):
```bash
# Create .env.local file
NEXT_PUBLIC_API_URL=http://localhost:8000
```

5. Run the development server:
```bash
npm run dev
```

The frontend will be available at `http://localhost:3000`

## Deployment

### Recommended: Railway (Backend) + Vercel (Frontend)

This is the recommended deployment setup:
- **Backend**: Deploy to Railway (Docker-based, supports persistent storage)
- **Frontend**: Deploy to Vercel (optimized for Next.js, CDN)

#### Deploy Backend to Railway

1. **Create a Railway project**:
   - Go to [Railway.app](https://railway.app) and sign up/login
   - Click "New Project" → "Deploy from GitHub repo"
   - Select your repository

2. **Configure the backend service**:
   - Railway will auto-detect the Dockerfile in `backend/Dockerfile`
   - The app automatically uses Railway's `PORT` environment variable (no configuration needed)
   - If not auto-detected, manually set:
     - **Root Directory**: Leave empty (builds from project root)
     - **Dockerfile Path**: `backend/Dockerfile`

3. **Set environment variables** in Railway:
   ```
   # Required: Service account (choose one method)
   GOOGLE_SERVICE_ACCOUNT_JSON={"type":"service_account",...}  # Recommended: JSON content as env var
   # OR
   SERVICE_ACCOUNT_PATH=/app/service-account.json  # If uploading file
   
   # Optional: LLM configuration
   LLM_MODEL=gemini-2.0-flash-exp
   LLM_MAX_TOKENS=1000
   
   # Optional: Vector store
   VECTOR_INDEX_PATH=/app/data/vector_index.index
   NEXTFLOW_DOCS_DIR=/app/nextflow-docs  # Auto-cloned during build
   ```

4. **Deploy**:
   - Railway will build and deploy automatically
   - Once deployed, copy the backend URL (e.g., `https://your-backend.railway.app`)

#### Deploy Frontend to Vercel

See [VERCEL_DEPLOYMENT.md](VERCEL_DEPLOYMENT.md) for detailed instructions.

**Quick steps**:
1. Connect your GitHub repo to Vercel
2. Set **Root Directory** to `frontend`
3. Set environment variable: `NEXT_PUBLIC_API_URL=https://your-backend.railway.app`
4. Deploy

The frontend will be available at a Vercel URL (e.g., `https://your-app.vercel.app`).

#### Configure CORS

The backend automatically allows Vercel domains via regex pattern (configured in `config.yaml`). For additional origins, add them to `config.yaml` → `cors.allowed_origins` or set `CORS_ORIGINS` environment variable.

### Alternative: Railway for Both (Full Stack)

You can also deploy both backend and frontend to Railway:

1. **Deploy backend** (see above)
2. **Add frontend service** in the same Railway project:
   - Set **Dockerfile Path**: `frontend/Dockerfile`
   - Set `NEXT_PUBLIC_API_URL=https://your-backend.railway.app`
3. **Update CORS** in `config.yaml` to include your Railway frontend URL

### Local Development with Docker

Run the entire stack locally with Docker Compose:

```bash
# Build and start both services
docker-compose up --build

# Backend will be at http://localhost:8000
# Frontend will be at http://localhost:3000
```

See `docker-compose.yml` for configuration details.

### Environment Variables Reference

**Backend** (Railway):
- `GOOGLE_SERVICE_ACCOUNT_JSON` - Service account JSON content as string (recommended)
- `SERVICE_ACCOUNT_PATH` - Path to service account JSON file (alternative to above)
- `LLM_MODEL` - Model name (default: `gemini-2.0-flash-exp`, override via env)
- `LLM_MAX_TOKENS` - Max output tokens (default: `1000`, override via env)
- `LLM_TEMPERATURE` - Model temperature (default: `0.7`, override via env)
- `VECTOR_INDEX_PATH` - Vector index path (default: `/app/data/vector_index.index`)
- `NEXTFLOW_DOCS_DIR` - Path to Nextflow docs (default: `/app/nextflow-docs`, auto-cloned)
- `CORS_ORIGINS` - Comma-separated list of allowed origins (optional, defaults in `config.yaml`)
- `PORT` - Server port (Railway sets automatically)

**Frontend** (Vercel/Railway):
- `NEXT_PUBLIC_API_URL` - Backend API URL (required for production)
- `NEXT_PUBLIC_LOADING_MESSAGES` - Comma-separated loading messages (optional)
- `NEXT_PUBLIC_MAX_INPUT_LENGTH` - Max input length (optional, default: 500000)

## Architecture Overview

```
┌─────────────┐         ┌──────────────┐         ┌─────────────┐
│   Frontend  │────────▶│   Backend    │────────▶│  Vector     │
│  (Next.js)  │  HTTP   │   (FastAPI)  │  Query  │   Store     │
│   (Vercel)  │         │  (Railway)   │         │   (FAISS)   │
└─────────────┘         └──────────────┘         └─────────────┘
                               │
                               ▼
                        ┌──────────────┐
                        │  Vertex AI   │
                        │   (Gemini)   │
                        └──────────────┘
```

**Data Flow**:
1. User sends message → Frontend
2. Frontend → Backend API (`/chat`)
3. Backend searches vector store for relevant docs
4. Backend calls Gemini LLM with context
5. Backend returns response with citations → Frontend
6. Frontend renders markdown response

**Notes**:
- Vector store index is built on first startup (may take a few minutes)
- Chat history is preserved within sessions but not persisted across restarts



## Testing

Run backend tests: 
```bash
cd backend
pytest test_*.py -v  # Run all tests
# Or run specific test files:
pytest test_main.py test_citations.py test_config.py test_vector_store.py test_llm_client.py -v
```

Run frontend tests: `cd frontend && npm test`

## License

MIT

