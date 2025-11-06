# Configuration Guide

The Nextflow Chat Assistant uses a shared `config.yaml` file for common configuration values, with environment variable overrides for deployment-specific settings.

## Configuration Files

- **`config.yaml`**: Shared configuration for both frontend and backend (single source of truth)
- **`backend/config.py`**: Backend config loader (reads from YAML + env vars)
- **`frontend/config.ts`**: Frontend config (auto-generated from YAML, can be overridden via env vars)

**Note**: The frontend config is auto-generated from `config.yaml`. After editing `config.yaml`, run:
```bash
cd frontend
npm run sync-config
```

Or it will auto-sync during `npm run build`.

## Shared Configuration (config.yaml)

The `config.yaml` file contains:

- **API Configuration**: API keys, base URLs, model names
- **LLM Configuration**: Model settings, temperature, max tokens
- **System Prompt**: The prompt used for all LLM interactions
- **Vector Store**: Document paths, index settings
- **Default Citations**: Fallback citation URLs
- **Frontend Settings**: Loading messages, API URLs

## Environment Variable Overrides

All values in `config.yaml` can be overridden via environment variables:

### Backend Environment Variables

```bash
# API (Required for Vertex AI)
export GOOGLE_CLOUD_PROJECT="your-gcp-project-id"  # Required!
export GOOGLE_VERTEX_API_KEY="your-key-here"

# LLM
export LLM_MODEL="vertex_ai/gemini-2.0-flash-exp"
export LLM_TEMPERATURE="0.7"
export LLM_MAX_TOKENS="500"

# Vector Store
export NEXTFLOW_DOCS_DIR="/path/to/docs"
export VECTOR_INDEX_PATH="./vector_index.index"
export VECTOR_SEARCH_TOP_K="5"
export VECTOR_SEARCH_THRESHOLD="0.5"
```

### Frontend Environment Variables

```bash
# API
export NEXT_PUBLIC_GOOGLE_VERTEX_API_KEY="your-key-here"
export NEXT_PUBLIC_GEMINI_API_BASE_URL="https://generativelanguage.googleapis.com/v1beta"
export NEXT_PUBLIC_GEMINI_MODEL="gemini-2.0-flash-exp"

# Frontend
export NEXT_PUBLIC_API_URL="http://localhost:8000"
export NEXT_PUBLIC_LOADING_MESSAGES="Thinking,Pondering,Noodling"
export NEXT_PUBLIC_SYSTEM_PROMPT="Custom prompt here"
```

## Priority Order

1. **Environment variables** (highest priority)
2. **config.yaml** (default/fallback)

## Editing Configuration

### For Development

Edit `config.yaml` directly. Changes take effect after restarting the services.

### For Production

Set environment variables in your deployment platform (Vercel, Railway, etc.). This keeps secrets out of code and allows per-environment configuration.

## Example: Changing the System Prompt

**Option 1: Edit config.yaml**
```yaml
system_prompt: |
  Your custom prompt here...
```

**Option 2: Use environment variable**
```bash
export NEXT_PUBLIC_SYSTEM_PROMPT="Your custom prompt here..."
```

## Example: Adding Loading Messages

**Edit config.yaml:**
```yaml
frontend:
  loading_messages:
    - "Thinking"
    - "Pondering"
    - "Your new message"
```

Or via environment variable:
```bash
export NEXT_PUBLIC_LOADING_MESSAGES="Thinking,Pondering,Your new message"
```

## Security Notes

- Never commit API keys to `config.yaml` in production
- Use environment variables for sensitive values
- The default API key in `config.yaml` is for development only
- In production, always set `GOOGLE_VERTEX_API_KEY` via environment variable

