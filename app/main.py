"""
FastAPI Main Application
RAG System with Document Indexing and Query Capabilities
"""

import os
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse
from contextlib import asynccontextmanager

from app.core.config import get_settings
from app.api.routes.health import router as health_router
from app.api.routes.documents import router as documents_router
from app.api.routes.chat import router as chat_router

settings = get_settings()


# ============================================================================
# LIFESPAN CONTEXT MANAGER
# ============================================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan events for startup and shutdown
    """
    # Startup
    print("="*70)
    print("RAG FastAPI System Starting...")
    print("="*70)
    
    # Ensure required directories exist
    os.makedirs(settings.CHROMA_DB_PATH, exist_ok=True)
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    os.makedirs("static", exist_ok=True)
    
    print(f"✓ ChromaDB path: {settings.CHROMA_DB_PATH}")
    print(f"✓ Upload directory: {settings.UPLOAD_DIR}")
    print(f"✓ Embedding model: {settings.EMBEDDING_MODEL}")
    print(f"✓ Chat model: {settings.CHAT_MODEL}")
    print("="*70)
    print(f"API running at: http://{settings.HOST}:{settings.PORT}")
    print(f"API docs at: http://{settings.HOST}:{settings.PORT}/docs")
    print(f"Admin UI at: http://{settings.HOST}:{settings.PORT}/admin")
    print(f"Chat UI at: http://{settings.HOST}:{settings.PORT}/chat")
    print("="*70)
    
    yield
    
    # Shutdown
    print("\nShutting down RAG FastAPI System...")


# ============================================================================
# FASTAPI APPLICATION
# ============================================================================

app = FastAPI(
    title="RAG FastAPI System",
    description="Document indexing and RAG-based question answering API",
    version="1.0.0",
    lifespan=lifespan
)


# ============================================================================
# CORS MIDDLEWARE
# ============================================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================================
# EXCEPTION HANDLERS
# ============================================================================

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler"""
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error": str(exc),
            "message": "An unexpected error occurred"
        }
    )


# ============================================================================
# ROUTE REGISTRATION
# ============================================================================

# API Routes
app.include_router(health_router)
app.include_router(documents_router)
app.include_router(chat_router)


# ============================================================================
# STATIC FILES & UI ROUTES
# ============================================================================

# Mount static files directory
if os.path.exists("static"):
    app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/", response_class=HTMLResponse)
async def root():
    """Root endpoint - API information"""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>RAG FastAPI System</title>
        <style>
            body {
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                max-width: 800px;
                margin: 50px auto;
                padding: 20px;
                background-color: #f5f5f5;
            }
            .container {
                background: white;
                padding: 40px;
                border-radius: 10px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            }
            h1 {
                color: #333;
                border-bottom: 3px solid #007bff;
                padding-bottom: 10px;
            }
            .links {
                margin-top: 30px;
            }
            .link-button {
                display: inline-block;
                padding: 12px 24px;
                margin: 10px 10px 10px 0;
                background-color: #007bff;
                color: white;
                text-decoration: none;
                border-radius: 5px;
                font-weight: bold;
                transition: background-color 0.3s;
            }
            .link-button:hover {
                background-color: #0056b3;
            }
            .info {
                margin-top: 20px;
                padding: 15px;
                background-color: #e7f3ff;
                border-left: 4px solid #007bff;
                border-radius: 4px;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🤖 RAG FastAPI System</h1>
            <p>Welcome to the RAG (Retrieval-Augmented Generation) FastAPI System.</p>
            
            <div class="info">
                <strong>Status:</strong> ✓ System Online<br>
                <strong>Version:</strong> 1.0.0
            </div>
            
            <div class="links">
                <h3>Available Interfaces:</h3>
                <a href="/docs" class="link-button">📚 API Documentation</a>
                <a href="/admin" class="link-button">⚙️ Admin Panel</a>
                <a href="/chat" class="link-button">💬 Chat Interface</a>
            </div>
            
            <div class="info" style="margin-top: 30px;">
                <h4>Quick Start:</h4>
                <ol>
                    <li>Go to <strong>Admin Panel</strong> to upload documents</li>
                    <li>Use <strong>Chat Interface</strong> to ask questions</li>
                    <li>Check <strong>API Documentation</strong> for programmatic access</li>
                </ol>
            </div>
        </div>
    </body>
    </html>
    """


@app.get("/admin", response_class=HTMLResponse)
async def admin_page():
    """Admin interface for document upload"""
    admin_html_path = "static/admin.html"
    
    if os.path.exists(admin_html_path):
        with open(admin_html_path, "r", encoding="utf-8") as f:
            return f.read()
    else:
        return """
        <!DOCTYPE html>
        <html>
        <head><title>Admin Panel</title></head>
        <body>
            <h1>Admin Panel</h1>
            <p>Admin interface will be available here.</p>
            <p>The static/admin.html file is not yet created.</p>
            <a href="/">← Back to Home</a>
        </body>
        </html>
        """


@app.get("/chat", response_class=HTMLResponse)
async def chat_page():
    """Chat interface"""
    chat_html_path = "static/chat.html"
    
    if os.path.exists(chat_html_path):
        with open(chat_html_path, "r", encoding="utf-8") as f:
            return f.read()
    else:
        return """
        <!DOCTYPE html>
        <html>
        <head><title>Chat Interface</title></head>
        <body>
            <h1>Chat Interface</h1>
            <p>Chat interface will be available here.</p>
            <p>The static/chat.html file is not yet created.</p>
            <a href="/">← Back to Home</a>
        </body>
        </html>
        """


# ============================================================================
# ENTRY POINT FOR RUNNING WITH UVICORN
# ============================================================================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=True
    )