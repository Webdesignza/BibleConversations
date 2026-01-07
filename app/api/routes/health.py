"""
Health Check Routes
System status and monitoring endpoints
"""

from fastapi import APIRouter
from app.models.schemas import HealthResponse
from app.services.indexing_service import get_indexing_service

router = APIRouter(prefix="/api/health", tags=["Health"])


@router.get("", response_model=HealthResponse)
async def health_check():
    """
    Check API health and vector store status
    
    Returns:
        Health status information
    """
    try:
        # Check vector store
        indexing_service = get_indexing_service()
        stats = indexing_service.get_vectorstore_stats()
        
        if stats["success"]:
            return HealthResponse(
                status="healthy",
                message="API is running",
                vector_store_status="connected",
                total_chunks=stats.get("total_chunks", 0)
            )
        else:
            return HealthResponse(
                status="degraded",
                message="API is running but vector store has issues",
                vector_store_status="error"
            )
            
    except Exception as e:
        return HealthResponse(
            status="unhealthy",
            message=f"Error: {str(e)}",
            vector_store_status="unknown"
        )