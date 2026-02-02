# ============================================================================
# Bible Conversations - ULTRA-OPTIMIZED for Railway Free Tier
# Dramatically reduces build time to avoid timeout
# ============================================================================

FROM python:3.11-slim

WORKDIR /app

# Install only essential system dependencies (minimal set)
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Copy requirements FIRST (for layer caching)
COPY requirements.txt .

# Install Python packages with aggressive optimization flags
# This is MUCH faster than the builder pattern
RUN pip install --no-cache-dir \
    --timeout=600 \
    --retries=5 \
    --disable-pip-version-check \
    -r requirements.txt

# Copy application code
COPY app/ ./app/
COPY static/ ./static/

# Create directories
RUN mkdir -p chroma_db uploads static/images

# Environment
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PORT=8009

# Expose port
EXPOSE 8009

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:${PORT}/health || exit 1

# Start app
CMD uvicorn app.main:app --host 0.0.0.0 --port ${PORT} --workers 1