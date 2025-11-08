FROM python:3.11-slim

WORKDIR /app

# Install minimal system dependencies
RUN apt-get update && apt-get install -y \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy config and check script first (needed for index check)
COPY config.yaml ./
COPY backend/config.py backend/check_index.py ./

# Copy backend directory (includes code, requirements, and optional index files)
COPY backend/ ./backend/

# Check if vector index exists in repo (before installing requirements)
RUN python check_index.py || echo "Index check: No index found (will need requirements-build-index.txt if building)"

# Install production requirements (always needed - minimal, no torch)
# This includes: FastAPI, uvicorn, google-genai, faiss-cpu, numpy
RUN pip install --no-cache-dir -r backend/requirements.txt

# Create persistent data directory first (needed for index files)
RUN mkdir -p /app/data

# Move backend code to app root (for uvicorn) and index files if they exist
RUN cp backend/main.py backend/llm_client.py backend/citations.py ./ && \
    cp -r backend/vector_store ./vector_store/ && \
    if [ -f backend/vector_index.index ] && [ -f backend/vector_index.data ]; then \
        cp backend/vector_index.index backend/vector_index.data /app/data/ && \
        echo "✓ Pre-built index files copied to /app/data/"; \
    else \
        echo "✗ No pre-built index files found in repo"; \
    fi

# Conditionally install build requirements only if BUILD_INDEX=true
# Production with pre-built index: BUILD_INDEX=false (skips torch/sentence-transformers)
# Building index at runtime: BUILD_INDEX=true (installs heavy dependencies)
ARG BUILD_INDEX=false
COPY backend/requirements-build-index.txt* ./
RUN if [ "$BUILD_INDEX" = "true" ] && [ -f requirements-build-index.txt ]; then \
    echo "BUILD_INDEX=true - Installing requirements-build-index.txt (torch, sentence-transformers)"; \
    pip install --no-cache-dir -r requirements-build-index.txt; \
    else \
    echo "BUILD_INDEX=false or index exists - Skipping requirements-build-index.txt"; \
    echo "  (Production runtime only needs requirements.txt - no torch needed)"; \
    fi

# Optional: Clone Nextflow docs only if BUILD_INDEX=true
ARG NEXTFLOW_BRANCH=master
RUN if [ "$BUILD_INDEX" = "true" ]; then \
    echo "Cloning Nextflow docs for index building..."; \
    git clone --depth 1 --branch ${NEXTFLOW_BRANCH} https://github.com/nextflow-io/nextflow.git /tmp/nextflow && \
    mv /tmp/nextflow/docs /app/nextflow-docs && \
    rm -rf /tmp/nextflow && \
    echo "Nextflow docs ready for index building"; \
    fi

# Verify final index status
RUN python check_index.py || echo "Final check completed"

EXPOSE 8000

# Start uvicorn on port 8000 (Railway handles port mapping)
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]

