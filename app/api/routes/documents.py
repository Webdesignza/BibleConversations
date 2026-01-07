"""
Document Management Routes
Endpoints for uploading and managing documents
"""

import os
import shutil
from pathlib import Path
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from typing import List

from app.core.config import get_settings
from app.core.security import verify_api_key
from app.models.schemas import DocumentUploadResponse, VectorStoreStatsResponse
from app.services.indexing_service import get_indexing_service

settings = get_settings()
router = APIRouter(prefix="/api/documents", tags=["Documents"])

# Ensure upload directory exists
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)


@router.post("/upload", response_model=DocumentUploadResponse, dependencies=[Depends(verify_api_key)])
async def upload_document(file: UploadFile = File(...)):
    """
    Upload and process a document
    
    Accepts: PDF, TXT, MD files
    
    Args:
        file: Document file to upload
        
    Returns:
        Upload result with processing statistics
    """
    # Validate file type
    allowed_extensions = ['.pdf', '.txt', '.md']
    file_extension = Path(file.filename).suffix.lower()
    
    if file_extension not in allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type. Allowed: {', '.join(allowed_extensions)}"
        )
    
    # Check file size (optional)
    max_size_bytes = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024
    
    try:
        # Save uploaded file temporarily
        file_path = os.path.join(settings.UPLOAD_DIR, file.filename)
        
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Check file size after saving
        file_size = os.path.getsize(file_path)
        if file_size > max_size_bytes:
            os.remove(file_path)
            raise HTTPException(
                status_code=413,
                detail=f"File too large. Max size: {settings.MAX_UPLOAD_SIZE_MB}MB"
            )
        
        # Process document
        indexing_service = get_indexing_service()
        result = indexing_service.process_document(file_path)
        
        # Clean up uploaded file (optional - you can keep it if needed)
        # os.remove(file_path)
        
        return DocumentUploadResponse(**result)
        
    except HTTPException:
        raise
    except Exception as e:
        # Clean up on error
        if os.path.exists(file_path):
            os.remove(file_path)
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")


@router.get("/stats", response_model=VectorStoreStatsResponse, dependencies=[Depends(verify_api_key)])
async def get_vector_store_stats():
    """
    Get vector store statistics
    
    Returns:
        Statistics about indexed documents
    """
    try:
        indexing_service = get_indexing_service()
        stats = indexing_service.get_vectorstore_stats()
        return VectorStoreStatsResponse(**stats)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get stats: {str(e)}")