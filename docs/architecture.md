# Architecture Overview

## System Components

**Frontend** (Next.js/React) → **Backend** (FastAPI) → **Vector Store** (FAISS) + **LLM** (Gemini)

## Request Flow

1. User sends message → Frontend validates and sends to `/chat`
2. Backend searches vector store for relevant docs
3. Backend calls Gemini LLM with query + context + conversation history
4. Backend returns response with citations → Frontend renders markdown

## Key Files

### Backend (`backend/`)
- **`main.py`** - FastAPI app, handles `/chat` endpoint
- **`config.py`** - Loads config from `config.yaml` + env vars
- **`models.py`** - Request/response models
- **`session_manager.py`** - In-memory conversation sessions
- **`llm_client.py`** - Google Vertex AI (Gemini) client
- **`llm_utils.py`** - Message building, system prompt
- **`vector_store_manager.py`** - Initializes vector store on startup
- **`citations.py`** - Extracts citations from search results
- **`security.py`** - Prompt injection detection (logs only)
- **`context_formatter.py`** - Formats search results for LLM
- **`logging_config.py`** - Logging setup (stdout/stderr routing)
- **`vector_store/`** - FAISS index, embeddings, document loading

### Frontend (`frontend/`)
- **`app/page.tsx`** - Main page component (composition container, < 100 lines)
- **`app/hooks/`** - Custom React hooks
  - `useChat.ts` - Chat state, message sending, session management
  - `useDarkMode.ts` - Dark mode state and localStorage
  - `useBackendHealth.ts` - Backend health polling
  - `useInput.ts` - Input state and character counting
  - `useLoadingMessage.ts` - Loading message rotation
- **`app/components/`** - UI components
  - `ChatHeader.tsx` - Header with theme toggle
  - `ChatMessages.tsx` - Messages container
  - `ChatMessage.tsx` - Individual message with markdown rendering
  - `ChatInput.tsx` - Input area with character counter
  - `EmptyState.tsx` - Welcome/empty state
  - `ErrorMessage.tsx` - Error display
  - `LoadingIndicator.tsx` - Loading state
  - `BackendUnavailableModal.tsx` - Backend unavailable modal
- **`app/types.ts`** - TypeScript interfaces
- **`app/utils.ts`** - Utility functions (chat history download)
- **`app/globals.css`** - Styles, theme, markdown styling
- **`config.ts`** - Auto-generated from `config.yaml`

### Configuration
- **`config.yaml`** - Shared config (API, LLM, vector store, CORS, frontend)
- Environment variables override YAML values

## Data Flow

```
Startup: Load config → Initialize vector store → Load/build index → Ready

Chat Request:
  User message → Validate → Get session → Search vector store → 
  Format context → Call LLM → Extract citations → Return response
```

## Deployment

- **Backend**: Railway (Docker) - auto-detects Dockerfile, uses `PORT` env var
- **Frontend**: Vercel (Next.js) - auto-detects, uses `NEXT_PUBLIC_API_URL`

## Key Design Decisions

- **Separation of concerns** - Small, focused modules
  - Backend: Modular Python modules (11 focused files)
  - Frontend: Custom hooks for logic, components for UI, page.tsx for composition
- **Single Responsibility Principle** - Each component/hook has one clear purpose
- **CPU-optimized** - Single-threaded embeddings for small servers
- **Configuration** - Centralized in `config.yaml` with env overrides
- **Error handling** - Clear messages, user messages preserved for download on error
