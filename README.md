# Nextflow Chat Assistant

**🌐 [Live Demo](https://nextflow-chatbot-git-main-nicholas-de-veauxs-projects.vercel.app?_vercel_share=DTofc9K3c2uHZqB3mInf0dJsfeWEBqcj)**

A chat assistant that answers Nextflow documentation questions using semantic search and LLM responses.

## Features

- **Multi-turn conversations** - Maintains context within sessions
- **Vector search** - Semantic search over Nextflow documentation with citations
- **Responsive UI** - Works on desktop and mobile devices (iOS-friendly)
- **Markdown rendering** - Rich text formatting for code blocks, links, lists
- **Error handling** - Graceful degradation with clear error messages
- **Loading states** - Animated loading indicators
- **Dark mode** - Theme toggle for user preference
- **Character limit** - Input validation with visual feedback
- **Security** - Light prompt injection detection

## Tech Stack

- **Frontend**: Next.js 14 with TypeScript, React, Markdown rendering
- **Backend**: FastAPI (Python) with async support
- **LLM**: Google Gemini 2.0 Flash via Vertex AI
- **Vector Store**: FAISS with sentence-transformers for semantic search
- **Deployment**: Railway (backend) + Vercel (frontend)

## Local Setup

See [Quick Start Guide](docs/quick-start.md) for local development setup instructions.

## Deployment

See [Deployment Guide](docs/deployment.md) for detailed deployment instructions.

## Author's Notes

### Process:

These **Author's Notes** are a chance for me to write unfiltered by compilers or llms!

Claude Code and Cursor were used extensively for the first half of the project (green field), but when it came to brown-field improvements, deployment optimization and troubleshooting, and the llm libraries, I had to work on those by hand. 

I chose python logic and sentence-transformers because I have experience with both of those libraries. I've only used typescript here and there before, but I like it, and wanted to try it -- however the frontend is where I relied the most on Claude. 

### Abandoned paths:

I had a scraper and started scraping the discussions on GitHub and Seqera’s site, in order to grow the embedded document corpus, but I came across a few roadblocks: it wasn’t immediately clear whether the Q&A was still relevant (on a recent version), whether the answer would be good enough to want to cite, and sometimes the question included stack traces that made it very long and not easily embeddable for vector search. So instead I tried to summarize as much as I could from those discussions into the main prompt.

I also previously had a check on GPU to see which version of torch to install, but once I was able to fit the CPU-version into Railway, I realized I could make the code simpler by making it always use the most minimal requirements doc (not having to download Nvidia libs). 

Also, since I used Railway and local development, I removed my docker-compose.yml file to have one less thing to maintain. 

### Compromises:

I was at first happy to have been able to put all my config in a .yaml, but then I realized Vercel only uses code in the front end directory, so I think in retrospect it might have been simpler to repeat my front-end config instead of trying to port it over from the yaml with config-porting scripts. 

I used Google’s LLM because I have a 90 day free trial with Google Cloud. In retrospect, it might have been interesting to test others, but my instinct is that it won’t make too much of a difference. In order to now become too enmeshed with it, I implemented conversation history tracking without having to rely on it to give me a conversation ID, which makes the gen-ai library more replaceable. 


## Project Structure

```
backend/
├── main.py                    # FastAPI app entry point
├── config.py                  # Configuration loader
├── models.py                  # Pydantic models
├── llm_client.py              # LLM client wrapper
├── llm_utils.py               # LLM utilities
├── session_manager.py         # Session management
├── security.py                # Security checks
├── context_formatter.py       # Context formatting
├── vector_store_manager.py    # Vector store initialization
├── citations.py               # Citation extraction
├── logging_config.py          # Logging setup
├── vector_store/              # Vector store implementation
├── requirements.txt           # Dependencies
├── Dockerfile                 # Backend Dockerfile
├── test_*.py                  # Unit tests
└── integration_test_chat.py   # Integration test for chat endpoint

frontend/
├── app/                       # Next.js app directory
│   ├── page.tsx               # Main page (composition container)
│   ├── layout.tsx             # Root layout
│   ├── globals.css            # Global styles
│   ├── types.ts               # TypeScript interfaces
│   ├── utils.ts               # Utility functions
│   ├── hooks/                 # Custom React hooks
│   │   ├── useChat.ts         # Chat state and message handling
│   │   ├── useDarkMode.ts     # Dark mode management
│   │   ├── useBackendHealth.ts # Backend health monitoring
│   │   ├── useInput.ts        # Input state and validation
│   │   └── useLoadingMessage.ts # Loading message rotation
│   └── components/            # UI components
│       ├── ChatHeader.tsx     # Header with theme toggle
│       ├── ChatMessages.tsx   # Messages container
│       ├── ChatMessage.tsx    # Individual message component
│       ├── ChatInput.tsx      # Input area with character counter
│       ├── EmptyState.tsx     # Welcome/empty state
│       ├── ErrorMessage.tsx   # Error display
│       ├── LoadingIndicator.tsx # Loading state
│       ├── BackendUnavailableModal.tsx # Backend unavailable modal
│       └── markdownComponents.tsx # Markdown renderer components
├── config.ts                  # Frontend config (auto-generated)
├── package.json               # Dependencies
├── Dockerfile                 # Frontend Dockerfile
├── scripts/
│   └── sync-config-standalone.js  # Config sync (Vercel)
└── __tests__/                 # Frontend tests

scripts/
└── sync-config.js             # Config sync (local/dev)

docs/                          # Documentation
├── architecture.md            # System architecture
├── deployment.md              # Deployment guide
├── quick-start.md             # Local development setup
├── vector-store.md            # Vector store documentation
└── ...                        # Other documentation

config.yaml                    # Shared configuration
README.md                      # Main documentation
```

See [Architecture Documentation](docs/architecture.md) for system architecture and component overview.

## Testing

### Backend Tests

**Unit tests:**
```bash
cd backend
pytest test_*.py -v  # Run all tests
# Or run specific test files:
pytest test_main.py test_citations.py test_config.py test_vector_store.py test_llm_client.py -v
```

**Integration test:**
```bash
cd backend
# Make sure the backend is running on http://localhost:8000
python integration_test_chat.py
```

This integration test:
- Tests the chat endpoint with sample questions
- Verifies session management (multi-turn conversations)
- Checks for citations in responses
- Validates backend health

### Frontend Tests

Run frontend tests: `cd frontend && npm test`

## License

MIT

