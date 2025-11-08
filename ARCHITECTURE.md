# Architecture Overview

This document explains how the Nextflow Chat Assistant is structured and how the different components work together.

## System Architecture

The application is a full-stack chat assistant with three main layers:

```
┌─────────────────────────────────────────────────────────────┐
│                         Frontend                             │
│  Next.js 14 (React, TypeScript) - User Interface           │
│  • Chat interface with markdown rendering                   │
│  • Session management (client-side)                         │
│  • Error handling and loading states                        │
└──────────────────────┬──────────────────────────────────────┘
                       │ HTTP Requests
                       ▼
┌─────────────────────────────────────────────────────────────┐
│                         Backend                              │
│  FastAPI (Python) - API Server                              │
│  • Request handling and validation                          │
│  • Session management (server-side)                         │
│  • Orchestrates vector search and LLM calls                 │
└──────────────┬──────────────────────────────┬───────────────┘
               │                              │
               ▼                              ▼
    ┌──────────────────┐          ┌──────────────────┐
    │  Vector Store    │          │   Vertex AI      │
    │  (FAISS)         │          │   (Gemini LLM)   │
    │  • Semantic      │          │   • Generates    │
    │    search        │          │     responses    │
    │  • Citations     │          │   • Uses context │
    └──────────────────┘          └──────────────────┘
```

## Request Flow

When a user asks a question:

1. **Frontend** (`frontend/app/page.tsx`)
   - User types message and clicks "Ask"
   - Validates input length
   - Sends POST request to `/chat` endpoint
   - Shows loading state with animated messages

2. **Backend** (`backend/main.py`)
   - Receives request at `/chat` endpoint
   - Validates message and checks for prompt injection
   - Manages session (creates or retrieves conversation history)
   - Searches vector store for relevant documentation
   - Calls LLM with user query, context, and conversation history
   - Extracts citations from search results
   - Returns response with citations

3. **Vector Store** (`backend/vector_store/`)
   - Searches FAISS index using semantic similarity
   - Returns top-k most relevant document chunks
   - Provides metadata (URLs, titles) for citations

4. **LLM** (`backend/llm_client.py`)
   - Receives user query, conversation history, and context
   - Uses system prompt (Nextflow-specific instructions)
   - Generates response using Gemini 2.0 Flash
   - Returns markdown-formatted answer

5. **Frontend** (back to `frontend/app/page.tsx`)
   - Receives response with citations
   - Renders markdown content (code blocks, links, lists)
   - Displays citations as superscript links
   - Adds message to conversation history

## Component Breakdown

### Backend Components (`backend/`)

#### Core Application
- **`main.py`** - FastAPI application entry point
  - Defines `/chat` and `/health` endpoints
  - Orchestrates request handling flow
  - Manages application lifecycle (startup/shutdown)

#### Configuration & Setup
- **`config.py`** - Configuration loader
  - Loads settings from `config.yaml`
  - Supports environment variable overrides
  - Handles service account authentication

- **`logging_config.py`** - Logging configuration
  - Routes DEBUG/INFO to stdout
  - Routes WARNING/ERROR to stderr
  - Suppresses verbose third-party library logs

#### Data Models
- **`models.py`** - Pydantic models
  - `ChatMessage` - Incoming user messages
  - `ChatResponse` - API response format

#### Session Management
- **`session_manager.py`** - Conversation session handling
  - Creates and tracks chat sessions
  - Stores conversation history in memory
  - Manages user and assistant messages

#### LLM Integration
- **`llm_client.py`** - Google Vertex AI client wrapper
  - Handles authentication (service account)
  - Makes API calls to Gemini
  - Manages response parsing

- **`llm_utils.py`** - LLM utility functions
  - Builds message arrays for API
  - Formats system prompt
  - Adds context to user queries

#### Vector Store
- **`vector_store_manager.py`** - Vector store initialization
  - Loads or builds FAISS index on startup
  - Manages vector store lifecycle
  - Handles graceful degradation if vector store unavailable

- **`vector_store/faiss_store.py`** - FAISS vector store implementation
  - Stores document embeddings
  - Performs semantic similarity search
  - Manages index persistence

- **`vector_store/embeddings.py`** - Embedding generation
  - Uses sentence-transformers (all-MiniLM-L6-v2)
  - Optimized for CPU (single-threaded)
  - Generates 384-dimensional embeddings

- **`vector_store/document_loader.py`** - Document processing
  - Loads markdown files from Nextflow docs
  - Chunks long documents
  - Extracts metadata (URLs, titles)

- **`vector_store/index_utils.py`** - Index utilities
  - Checks if index exists
  - Ensures index directory exists
  - Manages index file paths

#### Context & Citations
- **`context_formatter.py`** - Formats search results
  - Combines multiple search results into context
  - Removes duplicate URLs
  - Formats for LLM consumption

- **`citations.py`** - Citation extraction
  - Extracts URLs from search results
  - Formats citations for frontend
  - Provides fallback if vector store unavailable

#### Security
- **`security.py`** - Security checks
  - Detects potential prompt injection attempts
  - Logs suspicious patterns (doesn't block)
  - Lightweight guardrail

### Frontend Components (`frontend/`)

#### Core UI
- **`app/page.tsx`** - Main chat interface
  - Chat message display
  - Input handling with character counter
  - Loading states and error handling
  - Markdown rendering
  - Dark mode toggle
  - Backend health monitoring

- **`app/layout.tsx`** - Root layout
  - HTML structure
  - Metadata and fonts

- **`app/globals.css`** - Global styles
  - Theme variables (light/dark mode)
  - Markdown styling (code blocks, links, lists)
  - Responsive design (mobile-friendly)
  - iOS-specific fixes

#### Configuration
- **`config.ts`** - Frontend configuration
  - Auto-generated from `config.yaml`
  - API URL (overridden by `NEXT_PUBLIC_API_URL`)
  - Loading messages
  - Input length limits

#### Testing
- **`__tests__/page.test.tsx`** - Frontend tests
  - Component rendering tests
  - User interaction tests
  - Error handling tests

### Shared Configuration

#### Root Level
- **`config.yaml`** - Centralized configuration
  - API settings (service account, model)
  - LLM parameters (temperature, max tokens)
  - Vector store settings
  - CORS configuration
  - Frontend settings (loading messages, API URL)
  - System prompt (Nextflow documentation)

- **`docker-compose.yml`** - Local development
  - Defines backend and frontend services
  - Sets up networking
  - Configures volumes for persistence

- **`quick_start_local.sh`** - Quick setup script
  - Creates virtual environment
  - Installs dependencies
  - Provides setup instructions

## Data Flow

### Initialization (Application Startup)

1. **Backend startup** (`backend/main.py` → `lifespan`)
   - Loads configuration from `config.yaml`
   - Initializes logging
   - Checks if vector store is available
   - Loads or builds FAISS index
   - Initializes citation extractor
   - Starts FastAPI server

2. **Frontend startup** (`frontend/app/page.tsx`)
   - Loads configuration
   - Checks backend health
   - Initializes React state
   - Renders chat interface

### Chat Request Flow

```
User Input
    ↓
Frontend Validation (length, empty check)
    ↓
POST /chat → Backend
    ↓
Backend Validation (length, prompt injection check)
    ↓
Session Management (get/create session, load history)
    ↓
Vector Search (semantic similarity)
    ↓
Context Formatting (combine search results)
    ↓
LLM Call (Gemini with context + history)
    ↓
Citation Extraction (from search results)
    ↓
Response → Frontend
    ↓
Markdown Rendering
    ↓
Display to User
```

### Vector Store Flow

```
Application Startup
    ↓
Check if index exists (check_index.py)
    ↓
If exists: Load index → Ready
If not exists: Build index from docs → Ready
    ↓
Query Time:
    ↓
User query → Embed query → Search FAISS → Get top-k results
    ↓
Format results → Add to LLM context
```

## Key Design Decisions

### Separation of Concerns
- **Backend modules** are focused and single-purpose
- **Frontend components** handle UI only
- **Configuration** is centralized in `config.yaml`
- **Tests** are organized by module

### Error Handling
- **Graceful degradation** - App works without vector store (LLM-only mode)
- **Clear error messages** - Users see helpful error messages
- **Logging** - Structured logging for debugging

### Performance
- **CPU-optimized** - Single-threaded embeddings for small servers
- **Lazy loading** - Vector store only loads when needed
- **Index caching** - Index is built once and reused

### Security
- **Input validation** - Length limits, empty checks
- **Prompt injection detection** - Lightweight guardrails
- **CORS configuration** - Controlled API access
- **Environment variables** - Sensitive data in env vars

### User Experience
- **Markdown rendering** - Rich text formatting
- **Loading states** - Animated loading messages
- **Error recovery** - User messages preserved on error
- **Mobile-friendly** - Responsive design with iOS fixes
- **Dark mode** - User preference with persistence

## File Organization

```
nextflow_chatbot/
├── backend/                    # Backend API server
│   ├── main.py                # FastAPI app (orchestrates requests)
│   ├── config.py              # Configuration loader
│   ├── models.py              # Data models (ChatMessage, ChatResponse)
│   ├── llm_client.py          # LLM API client
│   ├── llm_utils.py           # LLM helper functions
│   ├── session_manager.py     # Session management
│   ├── security.py            # Security checks
│   ├── context_formatter.py   # Context formatting
│   ├── vector_store_manager.py # Vector store init
│   ├── citations.py           # Citation extraction
│   ├── logging_config.py      # Logging setup
│   ├── vector_store/          # Vector store implementation
│   │   ├── faiss_store.py     # FAISS index management
│   │   ├── embeddings.py      # Embedding generation
│   │   ├── document_loader.py # Document processing
│   │   └── index_utils.py     # Index utilities
│   ├── check_index.py         # Index existence check (Docker)
│   ├── requirements.txt       # Python dependencies
│   ├── Dockerfile             # Backend container
│   └── test_*.py              # Unit tests
│
├── frontend/                   # Frontend web app
│   ├── app/
│   │   ├── page.tsx           # Main chat interface
│   │   ├── layout.tsx         # Root layout
│   │   └── globals.css        # Global styles
│   ├── config.ts              # Frontend config (auto-generated)
│   ├── package.json           # Node.js dependencies
│   ├── Dockerfile             # Frontend container
│   └── __tests__/             # Frontend tests
│
├── scripts/                    # Utility scripts
│   └── sync-config.js         # Sync config.yaml to frontend
│
├── config.yaml                 # Shared configuration
├── docker-compose.yml          # Local development setup
├── quick_start_local.sh        # Quick setup script
└── README.md                   # Main documentation
```

## Configuration Management

All configuration is managed through `config.yaml` with environment variable overrides:

- **API Configuration** - Service account, model settings
- **LLM Configuration** - Temperature, max tokens, input limits
- **Vector Store** - Index path, search parameters
- **CORS** - Allowed origins, Vercel domain support
- **Frontend** - API URL, loading messages

Environment variables take precedence over YAML values, making it easy to configure for different environments (local, Railway, Vercel).

## Testing Strategy

### Backend Tests
- **Unit tests** for each module (`test_*.py`)
- **Integration test** for chat flow (`integration_test_chat.py`)
- **Test coverage** for core functionality

### Frontend Tests
- **Component tests** for main page (`__tests__/page.test.tsx`)
- **User interaction tests** - Button clicks, form submission
- **Error handling tests** - Backend unavailable, API errors

## Deployment Architecture

### Production (Railway + Vercel)
- **Backend**: Railway (Docker container)
  - Auto-detects Dockerfile
  - Uses `PORT` environment variable
  - Persistent storage for vector index
  - Automatic builds from GitHub

- **Frontend**: Vercel (Next.js)
  - Auto-detects Next.js
  - CDN for static assets
  - Environment variables for API URL
  - Automatic deployments

### Local Development
- **Backend**: `uvicorn main:app --reload`
- **Frontend**: `npm run dev`
- **Docker**: `docker-compose up` (optional)

## Scalability Considerations

- **Vector Store**: FAISS index is loaded in memory (fast queries)
- **Sessions**: In-memory storage (not persisted across restarts)
- **LLM Calls**: Async/await for non-blocking requests
- **Error Handling**: Graceful degradation if services unavailable
- **Caching**: Vector store index is cached after first load

## Future Improvements

- **Session Persistence**: Store sessions in database
- **Rate Limiting**: Add rate limiting for API endpoints
- **Caching**: Cache LLM responses for common queries
- **Monitoring**: Add metrics and monitoring
- **Authentication**: Add user authentication (optional)

