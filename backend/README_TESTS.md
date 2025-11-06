# Backend Tests

This directory contains tests for the Nextflow Chat Assistant backend.

## Running Tests

### Prerequisites

Install test dependencies:
```bash
pip install -r requirements.txt
```

### Run All Tests

```bash
pytest test_main.py -v
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

Tests are located in `test_main.py` and cover:

- **Health endpoint**: Basic health check
- **Chat endpoint**: Message sending and responses
- **Session management**: Multi-turn conversations
- **Citations**: Citation generation
- **Error handling**: Empty messages, invalid input
- **Knowledge context**: Vector store integration
- **Response structure**: Valid response format

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
- Mock mode can be enabled with `USE_MOCK_MODE=true` for faster tests

