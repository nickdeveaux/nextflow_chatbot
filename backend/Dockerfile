FROM python:3.11-slim

WORKDIR /app

# Install minimal system dependencies
RUN apt-get update && apt-get install -y \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy config and check script early (needed for index check)
COPY config.yaml ./
COPY backend/config.py backend/check_index.py ./

# Copy backend directory (includes code, requirements, and optional index files)
COPY backend/ ./backend/

# Install requirements (CPU-only) - needed for check_index.py
RUN pip install --no-cache-dir -r backend/requirements.txt

# Create persistent data directory (needed for index files)
RUN mkdir -p /app/data

# Move backend code to app root (for uvicorn) and index files if they exist
# Copy all Python modules that main.py depends on
RUN cp backend/main.py \
       backend/llm_client.py \
       backend/citations.py \
       backend/config.py \
       backend/logging_config.py \
       backend/models.py \
       backend/session_manager.py \
       backend/security.py \
       backend/llm_utils.py \
       backend/context_formatter.py \
       backend/vector_store_manager.py \
       ./ && \
    cp -r backend/vector_store ./vector_store/ && \
    if [ -f backend/vector_index.index ] && [ -f backend/vector_index.data ]; then \
        cp backend/vector_index.index backend/vector_index.data /app/data/ && \
        echo "✓ Pre-built index files copied to /app/data/"; \
    else \
        echo "✗ No pre-built index files found in repo"; \
    fi

# Check if index exists (in /app/data after copying from repo)
# If index exists, skip cloning docs (saves build time and image size)
# If index doesn't exist, clone docs so index can be built at runtime
ARG NEXTFLOW_BRANCH=master
RUN if python check_index.py; then \
        echo "✓ Index exists - skipping docs clone (index will be loaded at runtime)"; \
    else \
        echo "✗ Index not found - cloning docs for index build at runtime"; \
        git clone --depth 1 --branch ${NEXTFLOW_BRANCH} https://github.com/nextflow-io/nextflow.git /tmp/nextflow && \
        mv /tmp/nextflow/docs /app/nextflow-docs && \
        rm -rf /tmp/nextflow && \
        echo "✓ Nextflow docs cloned to /app/nextflow-docs"; \
    fi

# Set NEXTFLOW_DOCS_DIR environment variable
# If index exists: docs won't be cloned, but ENV is set (runtime won't need docs since index exists)
# If index doesn't exist: docs are cloned, ENV points to them (runtime will use docs to build index)
ENV NEXTFLOW_DOCS_DIR=/app/nextflow-docs

# Use PORT environment variable (Railway sets this automatically)
# Defaults to 8000 for local dev, but Railway will provide its own PORT
# EXPOSE is not needed - Railway handles port mapping automatically
CMD sh -c "uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}"

