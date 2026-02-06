# ============================================================================
# Bible Conversations - Universal (Railway + AWS Compatible)
# ============================================================================

FROM python:3.11-slim as builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --user \
    --timeout=1000 \
    --retries=10 \
    -r requirements.txt

# ============================================================================
# Final stage
# ============================================================================
FROM python:3.11-slim

WORKDIR /app

# Copy Python packages from builder
COPY --from=builder /root/.local /root/.local

# Install runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Copy application code
COPY app/ ./app/
COPY static/ ./static/

# Explicitly verify static files exist
RUN ls -la static/images/

# Add Python packages to PATH
ENV PATH=/root/.local/bin:$PATH

# Create necessary directories
RUN mkdir -p chroma_db uploads

# Environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Expose port (Railway ignores this but good for documentation)
EXPOSE ${PORT:-8080}

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:${PORT:-8080}/health || exit 1

# Start application - Uses Railway's PORT or defaults to 8080
CMD uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8080} --workers 1