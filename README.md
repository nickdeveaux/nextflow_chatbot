# Nextflow Chat Assistant

A simple TypeScript chat assistant that answers Nextflow documentation Q&A with light troubleshooting support.

## Features


- **Multi-turn conversations**: Maintains context within a session
- **Responsive UI**: Works on desktop and mobile devices
- **Vector search**: Semantic search over Nextflow documentation with citations
- **Light Prompt Injection check**: Prompt injection detection and logging
- **Error handling**: Graceful degradation with error messages
- **Docker support**: One-command deployment with docker-compose

## Tech Stack

- **Frontend**: Next.js 14 with TypeScript, React
- **Backend**: FastAPI (Python)
- **LLM**: Gemini 2.0 Flash via Google Vertex AI (using google-genai SDK)
- **Vector Store**: FAISS with sentence-transformers for semantic search (free, offline)
- **Deployment**: Docker containers, Railway-ready

## Local Setup

### Prerequisites

- Node.js 18+ and npm
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
# Required for Vertex AI (if not set in config.yaml):
export GOOGLE_CLOUD_PROJECT="your-gcp-project-id"

# Optional overrides:
export GOOGLE_VERTEX_API_KEY="your-key-here"
export NEXTFLOW_DOCS_DIR="/path/to/docs"
export VECTOR_INDEX_PATH="./vector_index.index"
```


**Note**: 
- Configuration is managed via `config.yaml` (shared between frontend/backend)
- See [CONFIG.md](./CONFIG.md) for detailed configuration guide
- The vector store will automatically build an index from your Nextflow docs on first run
- If the vector store is unavailable, the system will call Gemini directly

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

### Railway Deployment (Recommended)

Railway supports Docker deployments and is perfect for this full-stack application.

#### Prerequisites

- A [Railway](https://railway.app) account (free tier available)
- GitHub repository with your code
- Google Cloud service account JSON file for Vertex AI

#### Step 1: Deploy Backend to Railway

1. **Create a new Railway project**:
   - Go to [Railway.app](https://railway.app) and sign up/login
   - Click "New Project" → "Deploy from GitHub repo"
   - Select your repository

2. **Configure the backend service**:
   - Railway will auto-detect the Dockerfile in `backend/Dockerfile`
   - If not detected, manually set:
     - **Root Directory**: Leave empty (builds from project root)
     - **Dockerfile Path**: `backend/Dockerfile`
     - **Build Context**: Project root

3. **Set environment variables** in Railway dashboard:
   ```
   GOOGLE_CLOUD_PROJECT=your-gcp-project-id
   SERVICE_ACCOUNT_PATH=/app/service-account.json
   LLM_MODEL=gemini-2.0-flash-exp
   LLM_MAX_TOKENS=1000
   PORT=8000  # Railway sets this automatically, but can override
   ```

4. **Add service account file**:
   - In Railway, go to your service → Variables
   - Add a file variable named `SERVICE_ACCOUNT_JSON` with your service account JSON content
   - Or upload the file and Railway will handle it

5. **Deploy**:
   - Railway will automatically build and deploy
   - Once deployed, Railway will provide a URL like: `https://your-backend.railway.app`
   - Copy this URL for the frontend configuration

#### Step 2: Deploy Frontend to Railway

1. **Add a new service** in the same Railway project:
   - Click "New" → "GitHub Repo" (select the same repo)
   - Or add a service to the existing project

2. **Configure the frontend service**:
   - Set **Root Directory**: Leave empty
   - Set **Dockerfile Path**: `frontend/Dockerfile`
   - Railway will auto-detect Next.js

3. **Set environment variables**:
   ```
   NEXT_PUBLIC_API_URL=https://your-backend.railway.app
   PORT=3000  # Railway sets this automatically
   NODE_ENV=production
   ```

4. **Deploy**:
   - Railway will build and deploy the frontend
   - You'll get a URL like: `https://your-frontend.railway.app`

#### Step 3: Update CORS (if needed)

The backend already allows all origins (`allow_origins=["*"]`), but for production you may want to restrict it:

```python
# In backend/main.py, update CORS origins:
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://your-frontend.railway.app",  # Your Railway frontend URL
        "http://localhost:3000"  # For local dev
    ],
    ...
)
```

### Local Development with Docker

You can also run the entire stack locally with Docker Compose:

```bash
# Build and start both services
docker-compose up --build

# Backend will be at http://localhost:8000
# Frontend will be at http://localhost:3000
```

See `docker-compose.yml` for configuration details.

### Environment Variables Reference

**Backend** (Railway):
- `GOOGLE_CLOUD_PROJECT` - Your GCP project ID (required)
- `SERVICE_ACCOUNT_PATH` - Path to service account JSON (default: `/app/service-account.json`)
- `LLM_MODEL` - Model name (default: `gemini-2.0-flash-exp`)
- `LLM_MAX_TOKENS` - Max output tokens (default: `1000`)
- `PORT` - Server port (Railway sets automatically)

**Frontend** (Railway):
- `NEXT_PUBLIC_API_URL` - Backend API URL (required)
- `PORT` - Server port (Railway sets automatically)

## Demo URL

**Deployed URL**: [Add your Railway deployment URL here after deployment]

**Note**: 
- Vector store index is built on first startup (may take a few minutes)
- Chat history is preserved within sessions but not persisted across restarts


## Project Structure

```
nextflow_chatbot/
├── backend/
│   ├── main.py              # FastAPI application
│   └── requirements.txt     # Python dependencies
├── frontend/
│   ├── app/
│   │   ├── page.tsx         # Main chat interface
│   │   ├── layout.tsx       # Root layout
│   │   └── globals.css      # Styles
│   ├── package.json         # Node dependencies
│   └── tsconfig.json        # TypeScript config
└── README.md
```

## Configuration

The application uses a shared `config.yaml` file for common settings. See [CONFIG.md](./CONFIG.md) for detailed configuration guide.

### Quick Configuration

Most settings can be configured via environment variables (which override `config.yaml`):



All other settings (system prompt, loading messages, etc.) can be edited in `config.yaml`.

## Error Handling

The application handles:
- Network timeouts
- Invalid API responses
- Missing backend connections
- Graceful degradation to direct Gemini calls

## Testing

Run backend tests: `cd backend && pytest test_main.py -v`  
Run frontend tests: `cd frontend && npm test`

See [backend/README_TESTS.md](./backend/README_TESTS.md) and [frontend/README_TESTS.md](./frontend/README_TESTS.md) for details.

## License

MIT

