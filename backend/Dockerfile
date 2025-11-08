FROM python:3.11-slim

WORKDIR /app

# Install minimal system dependencies
RUN apt-get update && apt-get install -y \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy config and check scripts
COPY config.yaml ./
COPY backend/config.py backend/check_index.py ./

# Copy backend directory (includes code, requirements, and optional index files)
COPY backend/ ./backend/

# Check if vector index exists in repo
RUN python check_index.py || echo "Index check: No index found"

# Install requirements (CPU-only)
RUN pip install --no-cache-dir -r backend/requirements.txt

# Create persistent data directory first (needed for index files)
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

# Clone Nextflow docs for building index (only if BUILD_INDEX is true)
# This allows the index to be built at runtime if needed
ARG NEXTFLOW_BRANCH=master
ARG BUILD_INDEX=true
RUN if [ "$BUILD_INDEX" = "true" ]; then \
    echo "Cloning Nextflow docs for index building..."; \
    git clone --depth 1 --branch ${NEXTFLOW_BRANCH} https://github.com/nextflow-io/nextflow.git /tmp/nextflow && \
    mv /tmp/nextflow/docs /app/nextflow-docs && \
    rm -rf /tmp/nextflow && \
    echo "✓ Nextflow docs cloned to /app/nextflow-docs"; \
    else \
    echo "Skipping Nextflow docs clone (BUILD_INDEX=false)"; \
    fi

# Set NEXTFLOW_DOCS_DIR if docs were cloned
ENV NEXTFLOW_DOCS_DIR=/app/nextflow-docs

# Verify final index status
RUN python check_index.py || echo "Final check completed"

EXPOSE 8000

# Start uvicorn on port 8000 (Railway handles port mapping)
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]

