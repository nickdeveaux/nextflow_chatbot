FROM python:3.11-slim

WORKDIR /app

# Install system dependencies for sentence-transformers and git
RUN apt-get update && apt-get install -y \
    build-essential \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Clone Nextflow docs (shallow)
ARG NEXTFLOW_BRANCH=master
RUN git clone --depth 1 --branch ${NEXTFLOW_BRANCH} https://github.com/nextflow-io/nextflow.git /tmp/nextflow \
    && mv /tmp/nextflow/docs /app/nextflow-docs \
    && rm -rf /tmp/nextflow \
    && echo "Nextflow docs cloned from ${NEXTFLOW_BRANCH} branch"

# Copy backend code
COPY backend/main.py backend/config.py backend/llm_client.py backend/citations.py ./
COPY backend/vector_store/ ./vector_store/

# Copy shared config
COPY config.yaml ./

# Create persistent data directory
RUN mkdir -p /app/data

ENV NEXTFLOW_DOCS_DIR=/app/nextflow-docs

EXPOSE ${PORT:-8000}

CMD sh -c "uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}"

