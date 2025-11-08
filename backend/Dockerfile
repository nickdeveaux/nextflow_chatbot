FROM python:3.11-slim

WORKDIR /app

# Install minimal system dependencies
RUN apt-get update && apt-get install -y \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy config and check scripts
COPY config.yaml ./
COPY backend/config.py backend/check_index.py backend/check_gpu.py ./

# Copy backend directory (includes code, requirements, and optional index files)
COPY backend/ ./backend/

# Check if vector index exists in repo
RUN python check_index.py || echo "Index check: No index found"

# Install base requirements (CPU-only by default)
RUN pip install --no-cache-dir -r backend/requirements.txt

# Detect GPU and install GPU-accelerated packages if available
# Note: In Docker, GPU detection happens at runtime, not build time
# So we check via build arg or install both and let runtime choose
ARG USE_GPU=false
COPY backend/requirements-gpu.txt* ./
RUN if [ "$USE_GPU" = "true" ] && [ -f requirements-gpu.txt ]; then \
    echo "GPU mode enabled - Installing GPU-accelerated packages..."; \
    pip install --no-cache-dir -r requirements-gpu.txt; \
    echo "✓ GPU packages installed"; \
    else \
    echo "CPU-only mode - Using CPU-optimized packages from requirements.txt"; \
    fi

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

# Optional: Clone Nextflow docs for building index (if not using pre-built index)
ARG NEXTFLOW_BRANCH=master
ARG BUILD_INDEX=false
RUN if [ "$BUILD_INDEX" = "true" ]; then \
    echo "Building index - Cloning Nextflow docs..."; \
    git clone --depth 1 --branch ${NEXTFLOW_BRANCH} https://github.com/nextflow-io/nextflow.git /tmp/nextflow && \
    mv /tmp/nextflow/docs /app/nextflow-docs && \
    rm -rf /tmp/nextflow && \
    echo "✓ Nextflow docs ready for index building"; \
    fi

# Verify final index status
RUN python check_index.py || echo "Final check completed"

EXPOSE 8000

# Start uvicorn on port 8000 (Railway handles port mapping)
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]

