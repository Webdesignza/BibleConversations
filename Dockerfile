# ============================================================================
# Bible Conversations - Optimized for Railway Free Tier
# Faster builds with multi-stage build and caching
# ============================================================================

FROM python:3.11-slim as builder

# Set working directory
WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy only requirements first for better caching
COPY requirements.txt .

# Install dependencies with optimizations for faster build
RUN pip install --no-cache-dir --user \
    --timeout=1000 \
    --retries=10 \
    -r requirements.txt

# ============================================================================
# Final stage - smaller image
# ============================================================================
FROM python:3.11-slim

WORKDIR /app

# Copy Python packages from builder
COPY --from=builder /root/.local /root/.local

# Install only runtime dependencies (no build tools)
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy application code
COPY . .

# Make sure scripts are in PATH
ENV PATH=/root/.local/bin:$PATH

# Create necessary directories
RUN mkdir -p chroma_db uploads static/images

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PORT=8009

# Expose port
EXPOSE 8009

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:${PORT}/health || exit 1

# Start command
CMD uvicorn app.main:app --host 0.0.0.0 --port ${PORT}