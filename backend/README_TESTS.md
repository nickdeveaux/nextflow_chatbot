# Backend Tests

This directory contains tests for the Nextflow Chat Assistant backend.

## Running Tests

### Prerequisites

1. **Activate your virtual environment** (important!):
```bash
# Make sure you're in the backend directory
cd backend

# Activate virtual environment
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Verify you're using the correct Python
python --version  # Should match your venv Python
```

2. Install test dependencies:
```bash
pip install -r requirements.txt
```

### Run All Tests

**Important**: Make sure your virtual environment is activated first!

```bash
# Activate venv first
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Run all tests
pytest -v

# Or run specific test files
pytest test_main.py -v
pytest test_vector_store.py -v
pytest test_citations.py -v
pytest test_config.py -v
```


### Run Specific Tests

```bash
# Run only health endpoint test
pytest test_main.py::test_health_endpoint -v

# Run only chat endpoint tests
pytest test_main.py -k "chat" -v
```

### Run with Coverage

```bash
pytest test_main.py --cov=main --cov-report=html
```

## Test Structure

Tests are located in multiple files:

- **test_main.py**: Main API endpoint tests
  - Health endpoint
  - Chat endpoint (basic, session, citations)
  - Error handling
  - Response structure

- **test_citations.py**: Citation extraction tests
  - Initialization
  - Extraction with/without vector store
  - URL deduplication
  - Error handling

- **test_config.py**: Configuration tests
  - All config values are defined
  - Type validation
  - Environment variable overrides
  - Default values

- **test_vector_store.py**: Vector store functionality tests
  - Index building and initialization
  - Search functionality
  - Save/load operations
  - Metadata handling
  - Edge cases (empty index, single document, metadata mismatches)

- **test_llm_client.py**: LLM client tests
  - Initialization with defaults and custom params
  - Successful completion
  - System prompt handling
  - Error handling (empty responses, missing API keys)
  - Vertex AI credentials setup (JSON and file path)
  - Context manager usage

## Environment Variables

Tests use the default environment or can be configured:

```bash
export GOOGLE_VERTEX_API_KEY="your-key-here"
export NEXTFLOW_DOCS_DIR="/path/to/docs"
export VECTOR_INDEX_PATH="./test_index.index"
```

## Notes

- Tests may require the vector store to be initialized (first run may be slow)
- Some tests may make actual API calls to Gemini (ensure API key is set)
- Ensure you're using the correct Python environment (activate venv before running tests)

