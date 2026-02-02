import os
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
import secrets

from app.core.config import get_settings
from app.core.security import create_session
from app.api.routes import chat, documents, translations

settings = get_settings()

# Create FastAPI app
app = FastAPI(
    title="Bible Conversations API",
    description="Multi-Translation Bible Study System with RAG and Voice AI",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Include API routers
app.include_router(chat.router, prefix="/api/chat", tags=["chat"])
app.include_router(documents.router, prefix="/api/documents", tags=["documents"])
app.include_router(translations.router, prefix="/api/translations", tags=["translations"])

# Root endpoint
@app.get("/")
async def root():
    return HTMLResponse("""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Bible Conversations</title>
        <style>
            body {
                font-family: 'Segoe UI', sans-serif;
                background: linear-gradient(135deg, #1E3A8A 0%, #D97706 100%);
                min-height: 100vh;
                display: flex;
                align-items: center;
                justify-content: center;
                margin: 0;
            }
            .container {
                background: white;
                padding: 50px;
                border-radius: 20px;
                box-shadow: 0 10px 40px rgba(0,0,0,0.3);
                text-align: center;
                max-width: 600px;
            }
            h1 {
                color: #1E3A8A;
                margin-bottom: 20px;
            }
            .links {
                display: grid;
                grid-template-columns: 1fr 1fr;
                gap: 15px;
                margin-top: 30px;
            }
            a {
                display: block;
                padding: 15px 25px;
                background: linear-gradient(135deg, #1E3A8A 0%, #D97706 100%);
                color: white;
                text-decoration: none;
                border-radius: 10px;
                transition: transform 0.3s;
            }
            a:hover {
                transform: translateY(-2px);
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>📖 Bible Conversations</h1>
            <p>Multi-Translation Bible Study System</p>
            <div class="links">
                <a href="/static/bibleconversation.html">🎤 Bible Widget</a>
                <a href="/admin">⚙️ Admin Panel</a>
                <a href="/chat">💬 Chat Interface</a>
                <a href="/docs">📚 API Docs</a>
            </div>
        </div>
    </body>
    </html>
    """)

# Admin panel
@app.get("/admin")
async def admin():
    with open("static/admin.html", "r", encoding="utf-8") as f:
        return HTMLResponse(content=f.read())

# Chat interface
@app.get("/chat")
async def chat_page():
    with open("static/chat.html", "r", encoding="utf-8") as f:
        return HTMLResponse(content=f.read())

# Agent page (voice interface)
@app.get("/agent")
async def agent():
    # Generate session token
    token = secrets.token_urlsafe(32)
    
    # Register the session
    create_session(token)
    
    # Get the actual API base URL from environment or use localhost for local dev
    api_base = os.getenv("API_BASE_URL", "http://127.0.0.1:8080")
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Bible Study Agent</title>
        <script>
            const SESSION_TOKEN = "{token}";
            const API_BASE = "{api_base}";
        </script>
        <style>
            body {{
                font-family: 'Segoe UI', sans-serif;
                background: linear-gradient(135deg, #1E3A8A 0%, #D97706 100%);
                min-height: 100vh;
                display: flex;
                align-items: center;
                justify-content: center;
                margin: 0;
            }}
            .container {{
                background: white;
                padding: 40px;
                border-radius: 20px;
                box-shadow: 0 10px 40px rgba(0,0,0,0.3);
                text-align: center;
            }}
            h1 {{
                color: #1E3A8A;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>📖 Bible Study Agent</h1>
            <p>Session Active</p>
            <p>Token: <code>{token[:16]}...</code></p>
        </div>
    </body>
    </html>
    """
    return HTMLResponse(content=html)

# Health check - CRITICAL for App Runner
@app.get("/health")
async def health_check():
    """
    Health check endpoint for AWS App Runner.
    Must return 200 OK for the service to be considered healthy.
    """
    return {
        "status": "healthy",
        "service": "Bible Conversations",
        "version": "2.0.0"
    }

# Startup event
@app.on_event("startup")
async def startup_event():
    """
    Initialize services on startup.
    App Runner monitors this for successful startup.
    """
    print("🚀 Bible Conversations starting up...")
    print(f"📍 PORT: {os.getenv('PORT', '8080')}")
    print("✅ Ready to serve requests!")

# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    """
    Cleanup on shutdown.
    """
    print("👋 Bible Conversations shutting down...")

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8080))
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=port,
        workers=1,
        log_level="info"
    )