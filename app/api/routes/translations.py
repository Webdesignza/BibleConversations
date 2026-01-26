"""
API Routes for Bible Translation Management
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional
from app.core.security import verify_api_key
from app.services.rag_service import get_rag_service

router = APIRouter()


class CreateTranslationRequest(BaseModel):
    translation_id: str
    name: str
    description: Optional[str] = ""


class SwitchTranslationRequest(BaseModel):
    translation_id: str


@router.get("/list")
async def list_translations():  # Remove: api_key: str = Depends(verify_api_key)
    """Get list of all available Bible translations"""
    try:
        rag_service = get_rag_service()
        translations = rag_service.get_available_translations()
        
        return {
            'success': True,
            'translations': translations,
            'count': len(translations)
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to list translations: {str(e)}"
        )


@router.get("/current")
async def get_current_translation(api_key: str = Depends(verify_api_key)):
    """
    Get the currently active translation
    
    Returns:
        Current translation info or null if none selected
    """
    try:
        rag_service = get_rag_service()
        current = rag_service.get_current_translation()
        
        return {
            'success': True,
            'translation': current
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get current translation: {str(e)}"
        )


@router.post("/create")
async def create_translation(
    request: CreateTranslationRequest,
    api_key: str = Depends(verify_api_key)
):
    """
    Create a new Bible translation collection
    
    Args:
        request: Translation ID, name, and description
    
    Returns:
        Success status and message
    """
    try:
        rag_service = get_rag_service()
        result = rag_service.create_translation(
            translation_id=request.translation_id,
            name=request.name,
            description=request.description
        )
        
        if not result['success']:
            raise HTTPException(status_code=400, detail=result['message'])
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create translation: {str(e)}"
        )


@router.delete("/{translation_id}")
async def delete_translation(
    translation_id: str,
    api_key: str = Depends(verify_api_key)
):
    """
    Delete a Bible translation and its database
    
    Args:
        translation_id: ID of translation to delete
    
    Returns:
        Success status and message
    """
    try:
        rag_service = get_rag_service()
        result = rag_service.delete_translation(translation_id)
        
        if not result['success']:
            raise HTTPException(status_code=400, detail=result['message'])
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to delete translation: {str(e)}"
        )


@router.post("/switch")
async def switch_translation(
    request: SwitchTranslationRequest,
    api_key: str = Depends(verify_api_key)
):
    """
    Switch to a different Bible translation
    
    Args:
        request: Translation ID to switch to
    
    Returns:
        Success status and translation info
    """
    try:
        rag_service = get_rag_service()
        result = rag_service.switch_translation(request.translation_id)
        
        if not result['success']:
            raise HTTPException(status_code=400, detail=result['message'])
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to switch translation: {str(e)}"
        )