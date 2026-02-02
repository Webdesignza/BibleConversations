# ============================================================================
# Bible Conversations - Optimized for AWS App Runner
# Multi-stage build for minimal image size and faster cold starts
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

# Install Python dependencies to user site-packages
RUN pip install --no-cache-dir --user \
    --timeout=1000 \
    --retries=10 \
    -r requirements.txt

# ============================================================================
# Final stage - Minimal runtime image
# ============================================================================
FROM python:3.11-slim

WORKDIR /app

# Copy Python packages from builder
COPY --from=builder /root/.local /root/.local

# Install only essential runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Copy application code
COPY app/ ./app/
COPY static/ ./static/

# Add Python packages to PATH
ENV PATH=/root/.local/bin:$PATH

# Create necessary directories
RUN mkdir -p chroma_db uploads static/images

# App Runner specific environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# App Runner uses PORT environment variable (defaults to 8080)
ENV PORT=8080

# Expose port (App Runner ignores this but good for documentation)
EXPOSE 8080

# Health check for container health monitoring
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:${PORT}/health || exit 1

# Start application with optimized settings for App Runner
CMD uvicorn app.main:app \
    --host 0.0.0.0 \
    --port ${PORT} \
    --workers 1 \
    --loop uvloop \
    --no-access-log