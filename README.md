# Nextflow Chat Assistant

A simple TypeScript chat assistant that answers Nextflow documentation Q&A with light troubleshooting support.

## Features

- **Documentation Q&A (70%)**: Answers questions about Nextflow features, syntax, and capabilities
- **Troubleshooting (30%)**: Provides pragmatic guidance for common issues:
  - DSL1 vs DSL2 operator confusion
  - Executor configuration questions
  - Version checking and pinning
- **Multi-turn conversations**: Maintains context within a session
- **Responsive UI**: Works on desktop and mobile devices
- **Mock mode**: Works without API keys for demonstration

## Tech Stack

- **Frontend**: Next.js 14 with TypeScript, React
- **Backend**: FastAPI (Python)
- **LLM**: Gemini 2.5 via Google Vertex API (using litellm)
- **Vector Store**: FAISS with sentence-transformers for semantic search (free, offline)
- **Fallback**: Direct Gemini calls when vector store or backend unavailable

## Local Setup

### Prerequisites

- Node.js 18+ and npm
- Python 3.9+
- (Optional) OpenAI API key for full functionality

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

4. Set environment variables:
```bash
# Create .env file or export variables
export GOOGLE_VERTEX_API_KEY="REMOVED"  # Default key provided
export NEXTFLOW_DOCS_DIR="/Users/nickmarveaux/Dev/nextflow/docs"  # Path to Nextflow docs
export VECTOR_INDEX_PATH="./vector_index.index"  # Where to save vector index
```

**Note**: 
- The vector store will automatically build an index from your Nextflow docs on first run. This may take a few minutes. Subsequent starts will load the existing index.
- If the vector store is unavailable, the system will call Gemini directly with a Nextflow-specific prompt.
- The system uses Gemini 2.5 via Google Vertex API through litellm.

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

3. Set environment variables (optional):
```bash
# Create .env.local file
NEXT_PUBLIC_API_URL=http://localhost:8000
```

4. Run the development server:
```bash
npm run dev
```

The frontend will be available at `http://localhost:3000`

## Deployment

### Recommended: Vercel (Frontend) + Railway/Render (Backend)

This setup separates concerns and uses the best platform for each service.

#### Step 1: Deploy Backend to Railway (Recommended)

**Railway Setup**:
1. Go to [Railway.app](https://railway.app) and sign up/login
2. Click "New Project" → "Deploy from GitHub repo"
3. Select your repository
4. Railway will auto-detect Python. Configure:
   - **Root Directory**: `backend`
   - **Start Command**: `uvicorn main:app --host 0.0.0.0 --port $PORT`
5. Add environment variables in Railway dashboard:
   - `OPENAI_API_KEY` (optional, for full LLM functionality)
   - `USE_MOCK_MODE=true` (if not using API key)
   - `OPENAI_MODEL=gpt-4o-mini` (optional)
6. Railway will generate a URL like: `https://your-app.railway.app`
7. Copy this URL - you'll need it for the frontend

**Alternative: Render**:
1. Go to [Render.com](https://render.com) and sign up
2. Create a new "Web Service"
3. Connect your GitHub repository
4. Configure:
   - **Root Directory**: `backend`
   - **Environment**: Python 3
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn main:app --host 0.0.0.0 --port $PORT`
5. Add environment variables (same as Railway)
6. Render will give you a URL like: `https://your-app.onrender.com`

#### Step 2: Deploy Frontend to Vercel

**Vercel Setup**:
1. Go to [Vercel.com](https://vercel.com) and sign up/login
2. Click "Add New Project" → Import your GitHub repository
3. Configure:
   - **Root Directory**: `frontend`
   - **Framework Preset**: Next.js (auto-detected)
   - **Build Command**: `npm run build` (default)
   - **Output Directory**: `.next` (default)
4. Add environment variable:
   - `NEXT_PUBLIC_API_URL` = Your backend URL from Step 1
     - Example: `https://your-app.railway.app` or `https://your-app.onrender.com`
5. Click "Deploy"
6. Vercel will give you a URL like: `https://your-app.vercel.app`

**Important**: Update CORS in backend `main.py`:
```python
# In backend/main.py, update CORS origins:
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://your-app.vercel.app",  # Your Vercel URL
        "http://localhost:3000"  # For local dev
    ],
    ...
)
```

### Alternative Deployment Options

**All-in-one platforms** (deploy both services):
- **Render**: Can deploy both frontend and backend as separate services
- **Fly.io**: Deploy both with Docker
- **Heroku**: Use buildpacks (note: free tier discontinued)

**Cloud platforms**:
- **Google Cloud Run**: Deploy backend as container, frontend to Firebase Hosting
- **AWS**: Backend on ECS/Lambda, frontend on Amplify
- **Azure**: Backend on App Service, frontend on Static Web Apps

## Demo URL

**Deployed URL**: [Add your deployed URL here after deployment]

**Note**: The demo uses mock mode if no API key is configured, so it will work without OpenAI credentials.

See [DEPLOYMENT.md](./DEPLOYMENT.md) for detailed deployment instructions.

## Usage Examples

The assistant can handle questions like:

- "What is the latest version of Nextflow?"
- "Are from and into parts of DSL2 syntax?"
- "Does Nextflow support a Moab executor?"
- "What was that version again?" (follow-up)
- "Can you cite that?" (citations)

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

## Environment Variables

### Backend

- `GOOGLE_VERTEX_API_KEY`: Google Vertex API key for Gemini (default provided)
- `NEXTFLOW_DOCS_DIR`: Path to Nextflow documentation directory
- `VECTOR_INDEX_PATH`: Path where vector index is saved/loaded

### Frontend

- `NEXT_PUBLIC_API_URL`: Backend API URL (default: `http://localhost:8000`)
- `NEXT_PUBLIC_GOOGLE_VERTEX_API_KEY`: Google Vertex API key for direct Gemini calls (fallback)

## Error Handling

The application handles:
- Network timeouts
- Invalid API responses
- Missing backend connections
- Graceful degradation to mock mode

## Testing

See test documentation:
- **Backend tests**: [backend/README_TESTS.md](./backend/README_TESTS.md)
- **Frontend tests**: [frontend/README_TESTS.md](./frontend/README_TESTS.md)

Run backend tests:
```bash
cd backend
pytest test_main.py -v
```

Run frontend tests:
```bash
cd frontend
npm test
```

## Limitations

- No data persistence across app restarts
- No user authentication
- No cross-session history
- In-memory session storage only
- Vector store index must be rebuilt if docs change

## License

MIT

