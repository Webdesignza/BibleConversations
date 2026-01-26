"""
API Routes for Document Management (Translation-Specific)
"""

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from app.core.security import verify_api_key
from app.services.document_service import get_document_service
from app.services.rag_service import get_rag_service
import traceback

router = APIRouter()


@router.post("/{translation_id}/upload")
async def upload_document_to_translation(
    translation_id: str,
    file: UploadFile = File(...),
    api_key: str = Depends(verify_api_key)
):
    """
    Upload a document to a specific Bible translation
    
    Args:
        translation_id: ID of the translation to upload to
        file: Document file (PDF, TXT, MD, DOCX)
    
    Returns:
        Success status and number of chunks created
    """
    try:
        # Verify translation exists
        rag_service = get_rag_service()
        translations_metadata = rag_service._load_translations_metadata()
        
        if translation_id not in translations_metadata:
            raise HTTPException(
                status_code=404,
                detail=f"Translation '{translation_id}' not found"
            )
        
        # Process document for this specific translation
        doc_service = get_document_service()
        result = await doc_service.process_document(file, translation_id)
        
        if result['success']:
            # Update chunk count in metadata
            rag_service.update_translation_chunk_count(
                translation_id,
                result['total_chunks']
            )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"Upload failed: {str(e)}"
        )


@router.get("/{translation_id}/stats")
async def get_translation_stats(
    translation_id: str,
    api_key: str = Depends(verify_api_key)
):
    """
    Get statistics for a specific translation
    
    Args:
        translation_id: ID of the translation
    
    Returns:
        Translation statistics
    """
    try:
        rag_service = get_rag_service()
        translations_metadata = rag_service._load_translations_metadata()
        
        if translation_id not in translations_metadata:
            raise HTTPException(
                status_code=404,
                detail=f"Translation '{translation_id}' not found"
            )
        
        translation_info = translations_metadata[translation_id]
        
        return {
            'success': True,
            'translation_id': translation_id,
            'name': translation_info.get('name', translation_id),
            'total_chunks': translation_info.get('chunks', 0),
            'created': translation_info.get('created', ''),
            'description': translation_info.get('description', '')
        }
        
    except HTTPException:
        raise
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get stats: {str(e)}"
        )


@router.get("/stats")
async def get_all_stats(api_key: str = Depends(verify_api_key)):
    """
    Get statistics for all translations
    
    Returns:
        List of all translation statistics
    """
    try:
        rag_service = get_rag_service()
        translations = rag_service.get_available_translations()
        
        return {
            'success': True,
            'translations': translations,
            'total_translations': len(translations)
        }
        
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get stats: {str(e)}"
        )