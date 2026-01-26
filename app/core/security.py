from fastapi import HTTPException, Header, Depends
from typing import Optional
from app.core.config import get_settings

settings = get_settings()

# Simple in-memory session store (for development)
# In production, use Redis or a database
active_sessions = {}

def create_session(token: str):
    """Add a session token to active sessions"""
    active_sessions[token] = {'active': True}
    return token

def verify_session_token(token: str) -> bool:
    """Check if session token is valid"""
    return token in active_sessions and active_sessions[token].get('active', False)

async def verify_api_key(authorization: Optional[str] = Header(None)) -> str:
    """
    Verify API key or session token from Authorization header
    
    Accepts:
    - Static API key from .env (for admin operations)
    - Session tokens (for agent conversations)
    """
    
    if not authorization:
        raise HTTPException(
            status_code=401,
            detail="Missing authorization token"
        )
    
    # Extract token
    if authorization.startswith("Bearer "):
        token = authorization[7:]
    else:
        token = authorization
    
    # Check if it's the admin API key from .env
    if token == settings.API_KEY:
        return token
    
    # Check if it's a valid session token
    if verify_session_token(token):
        return token
    
    # Token is neither API key nor valid session
    raise HTTPException(
        status_code=401,
        detail="Invalid or expired authentication token"
    )