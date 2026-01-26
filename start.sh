#!/bin/bash

# ============================================================================
# Bible Conversations - Startup Script
# Used by Docker container to start the application
# ============================================================================

set -e

echo "=========================================="
echo "Bible Conversations - Starting Up"
echo "=========================================="

# Create required directories if they don't exist
mkdir -p chroma_db uploads static/images

echo "✓ Directories verified"

# Check required environment variables
if [ -z "$OPENAI_API_KEY" ]; then
    echo "❌ ERROR: OPENAI_API_KEY not set"
    exit 1
fi

if [ -z "$GROQ_API_KEY" ]; then
    echo "❌ ERROR: GROQ_API_KEY not set"
    exit 1
fi

if [ -z "$API_KEY" ]; then
    echo "❌ ERROR: API_KEY not set"
    exit 1
fi

echo "✓ Environment variables verified"

# Set default PORT if not provided by Railway
export PORT=${PORT:-8009}

echo "✓ Starting on port: $PORT"
echo "=========================================="

# Start the application with uvicorn
exec uvicorn app.main:app --host 0.0.0.0 --port $PORT