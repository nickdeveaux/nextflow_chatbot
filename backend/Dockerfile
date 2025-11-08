FROM python:3.11-slim

WORKDIR /app

# Install system dependencies for sentence-transformers
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY main.py config.py llm_client.py citations.py ./
COPY vector_store/ ./vector_store/

# Copy config files (assumes build context is project root)
COPY config.yaml nextflow_README.md ./

# Expose port (Railway will set PORT env var)
EXPOSE ${PORT:-8000}

# Use PORT environment variable for Railway compatibility
# Railway sets PORT automatically, default to 8000 if not set
CMD sh -c "uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}"

