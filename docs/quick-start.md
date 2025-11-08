# Quick Start Guide

## Prerequisites

- **Node.js 18.17 or later** and npm (Next.js 14 requires Node.js 18.17+)
- Python 3.9+

## Backend Setup

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

## Frontend Setup

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

