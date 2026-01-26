# ============================================================================
# Bible Conversations - Multi-Translation Bible Study System
# Docker Image for Railway Deployment
# ============================================================================

FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first (for layer caching)
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p chroma_db uploads static/images

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PORT=8009

# Expose port
EXPOSE 8009

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8009/health || exit 1

# Start command - Railway will inject $PORT
CMD uvicorn app.main:app --host 0.0.0.0 --port ${PORT}
