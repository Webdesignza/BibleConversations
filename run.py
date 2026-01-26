"""
Application runner script
"""

import sys
import os

# Get absolute path to project root
project_root = os.path.dirname(os.path.abspath(__file__))

# Add to Python path if not already there
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Also set PYTHONPATH environment variable
os.environ['PYTHONPATH'] = project_root

print("="*70)
print("Starting RAG FastAPI Server...")
print(f"Project root: {project_root}")
print(f"Python path: {sys.path[0]}")
print("="*70)

# Import and run
import uvicorn

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="127.0.0.1",
        port=8009,
        reload=True,
        reload_dirs=[project_root]
    )