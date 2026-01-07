"""
Chat/Query Routes
Endpoints for RAG-based question answering
"""

from fastapi import APIRouter, HTTPException, Depends

from app.core.security import verify_api_key
from app.models.schemas import ChatRequest, ChatResponse
from app.services.rag_service import get_rag_service

router = APIRouter(prefix="/api/chat", tags=["Chat"])


@router.post("", response_model=ChatResponse, dependencies=[Depends(verify_api_key)])
async def chat_query(request: ChatRequest):
    """
    Ask a question using RAG
    
    The system will:
    1. Retrieve relevant document chunks
    2. Generate an answer based on the context
    3. Return the answer with optional sources
    
    Args:
        request: Chat request with question and optional parameters
        
    Returns:
        Generated answer with sources
    """
    try:
        rag_service = get_rag_service()
        result = rag_service.query(
            question=request.question,
            k=request.k,
            include_sources=request.include_sources
        )
        
        if not result["success"]:
            raise HTTPException(status_code=500, detail=result.get("message", "Query failed"))
        
        return ChatResponse(**result)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Query failed: {str(e)}")