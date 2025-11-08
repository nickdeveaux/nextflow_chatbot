FROM python:3.11-slim

WORKDIR /app

# Install minimal system dependencies (no build-essential needed for CPU-only packages)
RUN apt-get update && apt-get install -y \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies (minimal - no ML libraries)
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend code
COPY backend/main.py backend/config.py backend/llm_client.py backend/citations.py ./
COPY backend/vector_store/ ./vector_store/

# Copy shared config
COPY config.yaml ./

# Copy pre-built vector index files if they exist (optional - for vector search)
# Note: If index files are committed to repo, uncomment these lines:
# COPY backend/vector_index.index ./vector_index.index
# COPY backend/vector_index.data ./vector_index.data

# Create persistent data directory
RUN mkdir -p /app/data

# Optional: Clone Nextflow docs only if needed for rebuilding index
# For production with pre-built index, this is not needed
ARG NEXTFLOW_BRANCH=master
ARG BUILD_VECTOR_STORE=false
RUN if [ "$BUILD_VECTOR_STORE" = "true" ]; then \
    git clone --depth 1 --branch ${NEXTFLOW_BRANCH} https://github.com/nextflow-io/nextflow.git /tmp/nextflow && \
    mv /tmp/nextflow/docs /app/nextflow-docs && \
    rm -rf /tmp/nextflow && \
    echo "Nextflow docs cloned from ${NEXTFLOW_BRANCH} branch"; \
    fi

EXPOSE ${PORT:-8000}

CMD sh -c "uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}"

