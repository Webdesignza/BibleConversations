"""
API Routes for Document Management (Translation-Specific)
UPDATED: Support for background processing with status tracking
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
    Returns immediately with job_id for tracking progress
    
    Args:
        translation_id: ID of the translation to upload to
        file: Document file (PDF, TXT, MD, DOCX)
    
    Returns:
        Success status with job_id for progress tracking
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
        
        # Start background processing
        doc_service = get_document_service()
        result = await doc_service.process_document(file, translation_id)
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"Upload failed: {str(e)}"
        )

@router.post("/{translation_id}/reset")
async def reset_translation(
    translation_id: str,
    api_key: str = Depends(verify_api_key)
):
    import shutil
    import stat
    from pathlib import Path
    from app.core.config import get_settings
    settings = get_settings()

    try:
        rag_service = get_rag_service()
        translations_metadata = rag_service._load_translations_metadata()

        if translation_id not in translations_metadata:
            raise HTTPException(status_code=404, detail=f"Translation '{translation_id}' not found")

        chroma_path = Path(settings.CHROMA_DB_PATH) / translation_id
        print(f"Resetting ChromaDB at: {chroma_path}")

        # Clear RAG service cache first
        if rag_service.current_translation == translation_id:
            rag_service.vectorstore = None
            rag_service.current_translation = None

        # Wipe directory - no PersistentClient
        if chroma_path.exists():
            shutil.rmtree(chroma_path)
            print(f"✓ Deleted directory: {chroma_path}")

        # Recreate with full permissions
        chroma_path.mkdir(parents=True, exist_ok=True)
        chroma_path.chmod(stat.S_IRWXU | stat.S_IRWXG | stat.S_IRWXO)
        print(f"✓ Recreated empty directory")

        # Reset chunk count in metadata
        translations_metadata[translation_id]['chunks'] = 0
        rag_service._save_translations_metadata(translations_metadata)

        return {
            'success': True,
            'message': f"Translation '{translation_id}' reset successfully.",
            'translation_id': translation_id
        }

    except HTTPException:
        raise
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Reset failed: {str(e)}")

@router.get("/upload-status/{job_id}")
async def get_upload_status(
    job_id: str,
    api_key: str = Depends(verify_api_key)
):
    """
    Check the status of a background upload job
    
    Args:
        job_id: Job ID returned from upload endpoint
    
    Returns:
        Current status, progress percentage, and message
    """
    try:
        doc_service = get_document_service()
        status = doc_service.get_processing_status(job_id)
        
        # If complete, update translation metadata
        if status.get('status') == 'complete':
            rag_service = get_rag_service()
            
            # Extract translation_id from job context if available
            # For now, we'll update all translations (safe but not ideal)
            # TODO: Store translation_id with job for precise updates
            translations = rag_service.get_available_translations()
            for trans in translations:
                # Refresh chunk count from ChromaDB
                try:
                    from langchain_chroma import Chroma
                    from pathlib import Path
                    trans_path = Path(rag_service.chroma_base_path) / trans['id']
                    if trans_path.exists():
                        vs = Chroma(
                            persist_directory=str(trans_path),
                            embedding_function=rag_service.embeddings
                        )
                        count = vs._collection.count()
                        rag_service.update_translation_chunk_count(trans['id'], count)
                except:
                    pass
        
        return {
            'success': True,
            **status
        }
        
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get status: {str(e)}"
        )


@router.post("/{translation_id}/reset")
async def reset_translation(
    translation_id: str,
    api_key: str = Depends(verify_api_key)
):
    import shutil
    import stat
    from pathlib import Path
    from app.core.config import get_settings
    settings = get_settings()

    try:
        rag_service = get_rag_service()
        translations_metadata = rag_service._load_translations_metadata()

        if translation_id not in translations_metadata:
            raise HTTPException(status_code=404, detail=f"Translation '{translation_id}' not found")

        chroma_path = Path(settings.CHROMA_DB_PATH) / translation_id
        print(f"Resetting ChromaDB at: {chroma_path}")

        # Step 1: Clear RAG service cache first
        if rag_service.current_translation == translation_id:
            rag_service.vectorstore = None
            rag_service.current_translation = None

        # Step 2: Wipe directory - no PersistentClient needed
        if chroma_path.exists():
            shutil.rmtree(chroma_path)
            print(f"✓ Deleted directory: {chroma_path}")

        # Step 3: Recreate with full permissions
        chroma_path.mkdir(parents=True, exist_ok=True)
        chroma_path.chmod(stat.S_IRWXU | stat.S_IRWXG | stat.S_IRWXO)
        print(f"✓ Recreated empty directory with 777 permissions")

        # Step 4: Reset chunk count in metadata
        translations_metadata[translation_id]['chunks'] = 0
        rag_service._save_translations_metadata(translations_metadata)

        return {
            'success': True,
            'message': f"Translation '{translation_id}' reset successfully.",
            'translation_id': translation_id
        }

    except HTTPException:
        raise
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Reset failed: {str(e)}")


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